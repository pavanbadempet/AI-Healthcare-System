"""Fix monitoring signal and appointment status constraints.

Revision ID: a43c2f91d7b0
Revises: 275039c926c9
Create Date: 2026-06-20 11:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a43c2f91d7b0"
down_revision: Union[str, Sequence[str], None] = "275039c926c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _constraint_names(constraints: list[dict]) -> set[str]:
    return {constraint["name"] for constraint in constraints if constraint.get("name")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    unique_names = _constraint_names(inspector.get_unique_constraints("monitoring_signals"))
    monitoring_changes = (
        "uq_monitoring_signal_patient_created" in unique_names
        or "uq_monitoring_signal_vital_type" not in unique_names
    )
    if monitoring_changes:
        with op.batch_alter_table("monitoring_signals", recreate="always") as batch_op:
            if "uq_monitoring_signal_patient_created" in unique_names:
                batch_op.drop_constraint(
                    "uq_monitoring_signal_patient_created",
                    type_="unique",
                )
            if "uq_monitoring_signal_vital_type" not in unique_names:
                batch_op.create_unique_constraint(
                    "uq_monitoring_signal_vital_type",
                    ["vital_observation_id", "signal_type"],
                )

    check_constraints = inspector.get_check_constraints("appointments")
    appointment_status = next(
        (
            constraint
            for constraint in check_constraints
            if constraint.get("name") == "check_appt_status"
        ),
        None,
    )
    if appointment_status is None or "Rescheduled" not in (appointment_status.get("sqltext") or ""):
        with op.batch_alter_table("appointments", recreate="always") as batch_op:
            if appointment_status is not None:
                batch_op.drop_constraint("check_appt_status", type_="check")
            batch_op.create_check_constraint(
                "check_appt_status",
                "status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled')",
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    unique_names = _constraint_names(inspector.get_unique_constraints("monitoring_signals"))
    with op.batch_alter_table("monitoring_signals", recreate="always") as batch_op:
        if "uq_monitoring_signal_vital_type" in unique_names:
            batch_op.drop_constraint("uq_monitoring_signal_vital_type", type_="unique")
        if "uq_monitoring_signal_patient_created" not in unique_names:
            batch_op.create_unique_constraint(
                "uq_monitoring_signal_patient_created",
                ["patient_id", "created_at"],
            )

    check_names = _constraint_names(inspector.get_check_constraints("appointments"))
    with op.batch_alter_table("appointments", recreate="always") as batch_op:
        if "check_appt_status" in check_names:
            batch_op.drop_constraint("check_appt_status", type_="check")
        batch_op.create_check_constraint(
            "check_appt_status",
            "status IN ('Scheduled', 'Completed', 'Cancelled')",
        )
