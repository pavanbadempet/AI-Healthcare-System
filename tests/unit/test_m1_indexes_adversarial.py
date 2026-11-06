"""
Unit test suite verifying Milestone 1 database indexing, composite query plans,
and check constraints.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql, sqlite

from backend.models import Base, ClinicalAICorrection
import backend.models as models_pkg
from backend.models.records import ChatLog
from backend.models.clinical import ClinicalOrder, CareEvent
from backend.models.appointments import Appointment
from backend.models.hospital import Encounter
from backend.models.intelligence import ClinicalAlert
from backend.models.pharmacy import PrescriptionItem, MedicationInventory
from backend.models.billing import BillingPayment


def test_clinical_ai_correction_export():
    """Verify ClinicalAICorrection is cleanly exported."""
    assert hasattr(ClinicalAICorrection, "__tablename__")
    assert ClinicalAICorrection.__tablename__ == "clinical_ai_corrections"
    assert "ClinicalAICorrection" in models_pkg.__all__


def test_all_foreign_keys_are_indexed():
    """Verify that every foreign key in Base.metadata.tables has an index."""
    unindexed_fks = []
    total_fks = 0
    for tbl_name, tbl in Base.metadata.tables.items():
        for col in tbl.columns:
            if col.foreign_keys:
                total_fks += 1
                is_indexed = col.index or any(col.name in [c.name for c in idx.columns] for idx in tbl.indexes)
                if not is_indexed:
                    unindexed_fks.append((tbl_name, col.name))

    assert total_fks > 0
    assert len(unindexed_fks) == 0, f"Found unindexed foreign keys: {unindexed_fks}"


def test_composite_indexes_declared():
    """Verify that all 5 composite indexes exist with expected columns."""
    expected_composites = {
        "chat_logs": ("idx_chat_logs_user_timestamp", ["user_id", "timestamp"]),
        "clinical_orders": ("idx_clinical_orders_patient_status", ["patient_id", "status"]),
        "appointments": ("idx_appointments_doctor_datetime", ["doctor_id", "date_time"]),
        "encounters": ("idx_encounters_patient_doctor", ["patient_id", "doctor_id"]),
        "clinical_alerts": ("idx_clinical_alerts_patient_ack_sev", ["patient_id", "is_acknowledged", "severity"]),
    }
    tables = Base.metadata.tables
    for tbl_name, (idx_name, cols) in expected_composites.items():
        assert tbl_name in tables, f"Table {tbl_name} missing"
        tbl = tables[tbl_name]
        idx_map = {idx.name: [c.name for c in idx.columns] for idx in tbl.indexes}
        assert idx_name in idx_map, f"Index {idx_name} missing from {tbl_name}"
        assert idx_map[idx_name] == cols, f"Columns for {idx_name} mismatch"


def test_sqlite_explain_query_plan_uses_indexes():
    """Verify SQLite EXPLAIN QUERY PLAN uses composite and foreign key indexes."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for i in range(10):
        session.add(ChatLog(user_id=1, role="user", content=f"msg {i}", timestamp=datetime.now(timezone.utc)))
        session.add(ClinicalOrder(patient_id=1, status="ordered", order_type="lab", title="CBC", priority="routine"))
        session.add(Appointment(user_id=1, doctor_id=2, specialist="Dr. Smith", date_time=datetime.now(timezone.utc), reason="Checkup", status="Scheduled"))
        session.add(Encounter(patient_id=1, doctor_id=2, status="open", encounter_type="OPD"))
        session.add(ClinicalAlert(patient_id=1, alert_type="vitals", severity="CRITICAL", message="High BP", is_acknowledged=False))
        session.add(PrescriptionItem(prescription_id=1, medication_name="Amoxicillin", inventory_id=10))
        session.add(CareEvent(patient_id=1, department_id=5, event_type="triage", title="Triage Check"))
        session.add(BillingPayment(invoice_id=1, patient_id=1, collected_by_id=3, amount=50.0, payment_method="card"))
    session.commit()

    explain_queries = [
        ("EXPLAIN QUERY PLAN SELECT * FROM chat_logs WHERE user_id = 1 ORDER BY timestamp DESC", "idx_chat_logs_user_timestamp"),
        ("EXPLAIN QUERY PLAN SELECT * FROM clinical_orders WHERE patient_id = 1 AND status = 'ordered'", "idx_clinical_orders_patient_status"),
        ("EXPLAIN QUERY PLAN SELECT * FROM appointments WHERE doctor_id = 2 AND date_time >= '2026-01-01'", "idx_appointments_doctor_datetime"),
        ("EXPLAIN QUERY PLAN SELECT * FROM encounters WHERE patient_id = 1 AND doctor_id = 2", "idx_encounters_patient_doctor"),
        ("EXPLAIN QUERY PLAN SELECT * FROM clinical_alerts WHERE patient_id = 1 AND is_acknowledged = 0 AND severity = 'CRITICAL'", "idx_clinical_alerts_patient_ack_sev"),
        ("EXPLAIN QUERY PLAN SELECT * FROM prescription_items WHERE inventory_id = 10", "ix_prescription_items_inventory_id"),
        ("EXPLAIN QUERY PLAN SELECT * FROM care_events WHERE department_id = 5", "ix_care_events_department_id"),
        ("EXPLAIN QUERY PLAN SELECT * FROM billing_payments WHERE collected_by_id = 3", "ix_billing_payments_collected_by_id"),
    ]

    with engine.connect() as conn:
        for q_sql, expected_idx in explain_queries:
            plan = conn.execute(text(q_sql)).fetchall()
            plan_str = " | ".join(str(p) for p in plan)
            assert expected_idx in plan_str, f"Plan did not use {expected_idx}: {plan_str}"


def test_medication_inventory_negative_stock_check_constraint():
    """Verify check constraint rejects negative stock."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    med_valid = MedicationInventory(
        facility_id=1,
        medication_name="Ibuprofen 200mg",
        batch_number="BATCH-001",
        quantity_on_hand=100.0,
        reorder_level=20.0,
    )
    session.add(med_valid)
    session.commit()

    med_invalid = MedicationInventory(
        facility_id=1,
        medication_name="Illegal Negative Stock",
        batch_number="BATCH-NEG",
        quantity_on_hand=-10.0,
        reorder_level=5.0,
    )
    session.add(med_invalid)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_with_for_update_dialect_parity():
    """Verify with_for_update compiles to FOR UPDATE in PG and cleanly in SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    q = session.query(MedicationInventory).with_for_update()
    sqlite_sql = str(q.statement.compile(dialect=sqlite.dialect()))
    pg_sql = str(q.statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE" not in sqlite_sql
    assert "FOR UPDATE" in pg_sql
