"""Add operational indexes and remove the legacy user-doctor column.

Revision ID: 275039c926c9
Revises: 4bccc856108e
Create Date: 2026-06-06 19:44:19.704842
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "275039c926c9"
down_revision: Union[str, Sequence[str], None] = "4bccc856108e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = (
    ("admissions", "ix_admissions_facility_id", ("facility_id",)),
    ("appointments", "ix_appointments_facility_id", ("facility_id",)),
    ("audit_logs", "ix_audit_logs_facility_id", ("facility_id",)),
    ("beds", "ix_beds_facility_id", ("facility_id",)),
    ("billable_services", "ix_billable_services_facility_id", ("facility_id",)),
    ("billing_payments", "ix_billing_payments_facility_id", ("facility_id",)),
    ("care_events", "ix_care_events_facility_id", ("facility_id",)),
    ("clinical_orders", "ix_clinical_orders_facility_id", ("facility_id",)),
    ("departments", "ix_departments_facility_id", ("facility_id",)),
    ("diagnostic_results", "ix_diagnostic_results_facility_id", ("facility_id",)),
    ("discharge_summaries", "ix_discharge_summaries_facility_id", ("facility_id",)),
    ("dispense_records", "ix_dispense_records_facility_id", ("facility_id",)),
    ("encounters", "ix_encounters_facility_id", ("facility_id",)),
    (
        "interoperability_consents",
        "ix_interoperability_consents_abdm_consent_id",
        ("abdm_consent_id",),
    ),
    (
        "interoperability_consents",
        "ix_interoperability_consents_abdm_request_id",
        ("abdm_request_id",),
    ),
    (
        "interoperability_consents",
        "ix_interoperability_consents_facility_id",
        ("facility_id",),
    ),
    (
        "interoperability_export_profiles",
        "ix_interoperability_export_profiles_facility_id",
        ("facility_id",),
    ),
    (
        "interoperability_exports",
        "ix_interoperability_exports_facility_id",
        ("facility_id",),
    ),
    ("invoices", "ix_invoices_facility_id", ("facility_id",)),
    (
        "medication_inventory",
        "ix_medication_inventory_facility_id",
        ("facility_id",),
    ),
    (
        "monitoring_signals",
        "ix_monitoring_signals_facility_id",
        ("facility_id",),
    ),
    ("nursing_tasks", "ix_nursing_tasks_facility_id", ("facility_id",)),
    ("prescriptions", "ix_prescriptions_facility_id", ("facility_id",)),
    ("users", "ix_users_facility_id", ("facility_id",)),
    (
        "vital_observations",
        "ix_vital_observations_facility_id",
        ("facility_id",),
    ),
)


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name) if index.get("name")}


def _drop_sqlite_users_batch_table(bind: sa.Connection) -> None:
    if bind.dialect.name == "sqlite":
        bind.execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_users"))


def _verify_sqlite_foreign_keys(bind: sa.Connection) -> None:
    violations = bind.execute(sa.text("PRAGMA foreign_key_check")).fetchall()
    if violations:
        raise RuntimeError(f"SQLite foreign key violations after users migration: {violations}")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, index_name, columns in INDEXES:
        if index_name not in _index_names(inspector, table_name):
            op.create_index(index_name, table_name, list(columns), unique=False)

    if bind.dialect.name != "sqlite":
        op.alter_column(
            "interoperability_consents",
            "abdm_last_event_at",
            existing_type=sa.TIMESTAMP(),
            type_=sa.DateTime(),
            existing_nullable=True,
        )

    if "doctor_id" in _column_names(inspector, "users"):
        if bind.dialect.name == "sqlite":
            _drop_sqlite_users_batch_table(bind)
            with op.batch_alter_table("users", recreate="always") as batch_op:
                batch_op.drop_column("doctor_id")
            _verify_sqlite_foreign_keys(bind)
        else:
            op.drop_column("users", "doctor_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "doctor_id" not in _column_names(inspector, "users"):
        if bind.dialect.name == "sqlite":
            _drop_sqlite_users_batch_table(bind)
            with op.batch_alter_table("users", recreate="always") as batch_op:
                batch_op.add_column(sa.Column("doctor_id", sa.Integer(), nullable=True))
            _verify_sqlite_foreign_keys(bind)
        else:
            op.add_column("users", sa.Column("doctor_id", sa.Integer(), nullable=True))

    if bind.dialect.name != "sqlite":
        op.alter_column(
            "interoperability_consents",
            "abdm_last_event_at",
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(),
            existing_nullable=True,
        )

    inspector = sa.inspect(bind)
    for table_name, index_name, _columns in reversed(INDEXES):
        if index_name in _index_names(inspector, table_name):
            op.drop_index(index_name, table_name=table_name)
