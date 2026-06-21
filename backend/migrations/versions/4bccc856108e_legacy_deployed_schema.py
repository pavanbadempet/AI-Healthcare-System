"""Bridge the legacy deployed database revision into the canonical history.

Revision ID: 4bccc856108e
Revises: 0001_baseline
Create Date: 2026-06-20 17:00:00.000000
"""

from typing import Sequence, Union

revision: str = "4bccc856108e"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Preserve the revision already stamped in deployed databases."""


def downgrade() -> None:
    """The bridge carries no schema operations."""
