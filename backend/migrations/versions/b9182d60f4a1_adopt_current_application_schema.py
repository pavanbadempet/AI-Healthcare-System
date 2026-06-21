"""Add soft-delete fields and ClinOS domain tables.

Revision ID: b9182d60f4a1
Revises: a43c2f91d7b0
Create Date: 2026-06-20 16:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b9182d60f4a1"
down_revision: Union[str, Sequence[str], None] = "a43c2f91d7b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SOFT_DELETE_TABLES = (
    "admissions",
    "appointments",
    "audit_logs",
    "chat_logs",
    "diagnostic_results",
    "encounters",
    "health_records",
    "prescriptions",
    "users",
    "vital_observations",
)


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
        if index.get("name")
    }


def _create_clinos_tables(existing_tables: set[str]) -> None:
    if "smart_apps" not in existing_tables:
        op.create_table(
            "smart_apps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("app_name", sa.String(), nullable=False, unique=True),
            sa.Column("client_id", sa.String(), nullable=False, unique=True),
            sa.Column("redirect_uri", sa.String(), nullable=False),
            sa.Column("launch_url", sa.String(), nullable=False),
            sa.Column(
                "scopes",
                sa.String(),
                nullable=True,
                server_default="launch/patient patient/*.read",
            ),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_smart_apps_id", "smart_apps", ["id"])
        op.create_index(
            "ix_smart_apps_client_id",
            "smart_apps",
            ["client_id"],
            unique=True,
        )

    if "smart_launch_contexts" not in existing_tables:
        op.create_table(
            "smart_launch_contexts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "app_id",
                sa.Integer(),
                sa.ForeignKey("smart_apps.id"),
                nullable=False,
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("launch_token", sa.String(), nullable=False, unique=True),
            sa.Column("auth_code", sa.String(), nullable=True),
            sa.Column("scope", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_smart_launch_contexts_id", "smart_launch_contexts", ["id"])
        op.create_index(
            "ix_smart_launch_contexts_app_id",
            "smart_launch_contexts",
            ["app_id"],
        )
        op.create_index(
            "ix_smart_launch_contexts_patient_id",
            "smart_launch_contexts",
            ["patient_id"],
        )
        op.create_index(
            "ix_smart_launch_contexts_user_id",
            "smart_launch_contexts",
            ["user_id"],
        )
        op.create_index(
            "ix_smart_launch_contexts_launch_token",
            "smart_launch_contexts",
            ["launch_token"],
            unique=True,
        )

    if "model_feedbacks" not in existing_tables:
        op.create_table(
            "model_feedbacks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("model_name", sa.String(), nullable=False),
            sa.Column("input_features", sa.Text(), nullable=False),
            sa.Column("prediction_result", sa.Text(), nullable=False),
            sa.Column("corrected_label", sa.String(), nullable=False),
            sa.Column(
                "clinician_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("status", sa.String(), nullable=True, server_default="pending_sync"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_model_feedbacks_id", "model_feedbacks", ["id"])
        op.create_index(
            "ix_model_feedbacks_patient_id",
            "model_feedbacks",
            ["patient_id"],
        )
        op.create_index(
            "ix_model_feedbacks_clinician_id",
            "model_feedbacks",
            ["clinician_id"],
        )
        op.create_index(
            "ix_model_feedbacks_model_name",
            "model_feedbacks",
            ["model_name"],
        )

    if "federated_sync_audits" not in existing_tables:
        op.create_table(
            "federated_sync_audits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sync_run_id", sa.String(), nullable=False, unique=True),
            sa.Column("node_id", sa.String(), nullable=False),
            sa.Column("model_name", sa.String(), nullable=False),
            sa.Column("records_synced", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("epsilon_consumed", sa.Float(), nullable=False, server_default="0"),
            sa.Column("delta_consumed", sa.Float(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index(
            "ix_federated_sync_audits_id",
            "federated_sync_audits",
            ["id"],
        )
        op.create_index(
            "ix_federated_sync_audits_sync_run_id",
            "federated_sync_audits",
            ["sync_run_id"],
            unique=True,
        )
        op.create_index(
            "ix_federated_sync_audits_model_name",
            "federated_sync_audits",
            ["model_name"],
        )

    if "clinical_alerts" not in existing_tables:
        op.create_table(
            "clinical_alerts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("alert_type", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("source_event_id", sa.String(), nullable=True),
            sa.Column(
                "is_acknowledged",
                sa.Boolean(),
                nullable=True,
                server_default=sa.false(),
            ),
            sa.Column(
                "acknowledged_by",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
            sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_clinical_alerts_id", "clinical_alerts", ["id"])
        op.create_index(
            "ix_clinical_alerts_patient_id",
            "clinical_alerts",
            ["patient_id"],
        )
        op.create_index(
            "ix_clinical_alerts_alert_type",
            "clinical_alerts",
            ["alert_type"],
        )

    if "patient_insights" not in existing_tables:
        op.create_table(
            "patient_insights",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("insight_type", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("model_version", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_patient_insights_id", "patient_insights", ["id"])
        op.create_index(
            "ix_patient_insights_patient_id",
            "patient_insights",
            ["patient_id"],
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in SOFT_DELETE_TABLES:
        columns = _column_names(inspector, table_name)
        if "is_deleted" not in columns:
            op.add_column(
                table_name,
                sa.Column(
                    "is_deleted",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
            )
        if "deleted_at" not in columns:
            op.add_column(
                table_name,
                sa.Column("deleted_at", sa.DateTime(), nullable=True),
            )

        inspector = sa.inspect(bind)
        index_name = f"ix_{table_name}_is_deleted"
        if index_name not in _index_names(inspector, table_name):
            op.create_index(index_name, table_name, ["is_deleted"])

    _create_clinos_tables(existing_tables)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in (
        "patient_insights",
        "clinical_alerts",
        "federated_sync_audits",
        "model_feedbacks",
        "smart_launch_contexts",
        "smart_apps",
    ):
        if table_name in existing_tables:
            op.drop_table(table_name)

    for table_name in reversed(SOFT_DELETE_TABLES):
        columns = _column_names(sa.inspect(bind), table_name)
        index_name = f"ix_{table_name}_is_deleted"
        if index_name in _index_names(sa.inspect(bind), table_name):
            op.drop_index(index_name, table_name=table_name)
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table(table_name, recreate="always") as batch_op:
                if "deleted_at" in columns:
                    batch_op.drop_column("deleted_at")
                if "is_deleted" in columns:
                    batch_op.drop_column("is_deleted")
        else:
            if "deleted_at" in columns:
                op.drop_column(table_name, "deleted_at")
            if "is_deleted" in columns:
                op.drop_column(table_name, "is_deleted")
