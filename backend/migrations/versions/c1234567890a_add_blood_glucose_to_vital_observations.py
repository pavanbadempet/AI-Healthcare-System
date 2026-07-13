"""add blood glucose to vital observations

Revision ID: c1234567890a
Revises: b9182d60f4a1
Create Date: 2026-06-21 19:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1234567890a"
down_revision: Union[str, Sequence[str], None] = "b9182d60f4a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("vital_observations")]
    if "blood_glucose" not in columns:
        op.add_column("vital_observations", sa.Column("blood_glucose", sa.Float(), nullable=True))

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("vital_observations")]
    if "blood_glucose" in columns:
        with op.batch_alter_table("vital_observations") as batch_op:
            batch_op.drop_column("blood_glucose")
