"""Add foreign key and composite indexes for Milestone 1 optimization.

Revision ID: d234567890ab
Revises: c1234567890a
Create Date: 2026-11-06 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d234567890ab"
down_revision: Union[str, Sequence[str], None] = "c1234567890a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# List of (index_name, table_name, [columns]) for single-column foreign keys
FK_INDEXES = [
    # billing.py
    ("ix_billable_services_department_id", "billable_services", ["department_id"]),
    ("ix_invoices_created_by_id", "invoices", ["created_by_id"]),
    ("ix_invoice_line_items_service_id", "invoice_line_items", ["service_id"]),
    ("ix_billing_payments_collected_by_id", "billing_payments", ["collected_by_id"]),
    # clinical.py
    ("ix_clinical_orders_department_id", "clinical_orders", ["department_id"]),
    ("ix_care_events_actor_user_id", "care_events", ["actor_user_id"]),
    ("ix_care_events_department_id", "care_events", ["department_id"]),
    ("ix_vital_observations_recorded_by_id", "vital_observations", ["recorded_by_id"]),
    ("ix_vital_observations_department_id", "vital_observations", ["department_id"]),
    ("ix_monitoring_signals_department_id", "monitoring_signals", ["department_id"]),
    ("ix_diagnostic_results_department_id", "diagnostic_results", ["department_id"]),
    ("ix_diagnostic_results_reviewed_by_id", "diagnostic_results", ["reviewed_by_id"]),
    # hospital.py
    ("ix_beds_department_id", "beds", ["department_id"]),
    ("ix_encounters_department_id", "encounters", ["department_id"]),
    ("ix_admissions_doctor_id", "admissions", ["doctor_id"]),
    ("ix_admissions_department_id", "admissions", ["department_id"]),
    ("ix_admissions_bed_id", "admissions", ["bed_id"]),
    # intelligence.py
    ("ix_clinical_alerts_acknowledged_by", "clinical_alerts", ["acknowledged_by"]),
    # interoperability.py
    ("ix_interoperability_consents_granted_by_id", "interoperability_consents", ["granted_by_id"]),
    ("ix_interoperability_consents_revoked_by_id", "interoperability_consents", ["revoked_by_id"]),
    ("ix_interoperability_export_profiles_department_id", "interoperability_export_profiles", ["department_id"]),
    ("ix_interoperability_export_profiles_created_by_id", "interoperability_export_profiles", ["created_by_id"]),
    ("ix_interoperability_exports_requested_by_id", "interoperability_exports", ["requested_by_id"]),
    ("ix_interoperability_exports_consent_id", "interoperability_exports", ["consent_id"]),
    ("ix_interoperability_exports_profile_id", "interoperability_exports", ["profile_id"]),
    # nursing.py
    ("ix_nursing_tasks_created_by_id", "nursing_tasks", ["created_by_id"]),
    ("ix_nursing_tasks_completed_by_id", "nursing_tasks", ["completed_by_id"]),
    ("ix_nursing_tasks_department_id", "nursing_tasks", ["department_id"]),
    # pharmacy.py
    ("ix_prescription_items_inventory_id", "prescription_items", ["inventory_id"]),
    ("ix_dispense_records_inventory_id", "dispense_records", ["inventory_id"]),
    ("ix_dispense_records_dispensed_by_id", "dispense_records", ["dispensed_by_id"]),
]

# List of (index_name, table_name, [columns]) for high-frequency composite queries
COMPOSITE_INDEXES = [
    ("idx_chat_logs_user_timestamp", "chat_logs", ["user_id", "timestamp"]),
    ("idx_clinical_orders_patient_status", "clinical_orders", ["patient_id", "status"]),
    ("idx_appointments_doctor_datetime", "appointments", ["doctor_id", "date_time"]),
    ("idx_encounters_patient_doctor", "encounters", ["patient_id", "doctor_id"]),
    ("idx_clinical_alerts_patient_ack_sev", "clinical_alerts", ["patient_id", "is_acknowledged", "severity"]),
]


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
        if index.get("name")
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Create clinical_ai_corrections table if not existing
    if "clinical_ai_corrections" not in existing_tables:
        op.create_table(
            "clinical_ai_corrections",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("clinician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("function_name", sa.String(), nullable=False),
            sa.Column("original_ai_output", sa.Text(), nullable=False),
            sa.Column("corrected_output", sa.Text(), nullable=True),
            sa.Column("override_action", sa.String(), nullable=False),
            sa.Column("override_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_clinical_ai_corrections_id", "clinical_ai_corrections", ["id"])
        op.create_index("ix_clinical_ai_corrections_patient_id", "clinical_ai_corrections", ["patient_id"])
        op.create_index("ix_clinical_ai_corrections_clinician_id", "clinical_ai_corrections", ["clinician_id"])
        op.create_index("ix_clinical_ai_corrections_function_name", "clinical_ai_corrections", ["function_name"])
        existing_tables.add("clinical_ai_corrections")

    # 2. Apply 31 Foreign Key Indexes
    for index_name, table_name, columns in FK_INDEXES:
        if table_name in existing_tables:
            current_indexes = _index_names(inspector, table_name)
            if index_name not in current_indexes:
                op.create_index(index_name, table_name, columns)

    # 3. Apply 5 High-Frequency Composite Indexes
    for index_name, table_name, columns in COMPOSITE_INDEXES:
        if table_name in existing_tables:
            current_indexes = _index_names(inspector, table_name)
            if index_name not in current_indexes:
                op.create_index(index_name, table_name, columns)

    # 4. Apply CheckConstraint on medication_inventory
    if "medication_inventory" in existing_tables:
        existing_checks = {c.get("name") for c in inspector.get_check_constraints("medication_inventory")}
        if "check_inventory_quantity_non_negative" not in existing_checks:
            with op.batch_alter_table("medication_inventory") as batch_op:
                batch_op.create_check_constraint(
                    "check_inventory_quantity_non_negative",
                    "quantity_on_hand >= 0",
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Drop check constraint on medication_inventory
    if "medication_inventory" in existing_tables:
        existing_checks = {c.get("name") for c in inspector.get_check_constraints("medication_inventory")}
        if "check_inventory_quantity_non_negative" in existing_checks:
            with op.batch_alter_table("medication_inventory") as batch_op:
                batch_op.drop_constraint("check_inventory_quantity_non_negative", type_="check")

    # 2. Drop 5 Composite Indexes and 31 Foreign Key Indexes
    all_indexes = COMPOSITE_INDEXES + FK_INDEXES
    for index_name, table_name, _ in all_indexes:
        if table_name in existing_tables:
            current_indexes = _index_names(inspector, table_name)
            if index_name in current_indexes:
                op.drop_index(index_name, table_name=table_name)

    # 3. Drop clinical_ai_corrections if present
    if "clinical_ai_corrections" in existing_tables:
        op.drop_table("clinical_ai_corrections")
