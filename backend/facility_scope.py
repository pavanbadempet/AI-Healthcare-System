"""Shared facility-boundary checks for role-scoped clinical access."""

from __future__ import annotations

from sqlalchemy.orm import Session

from . import models


def users_share_facility_context(db: Session, first_user_id: int, second_user_id: int) -> bool:
    """Return False when both users are explicitly assigned to different facilities."""
    users = db.query(models.User.id, models.User.facility_id).filter(
        models.User.id.in_([first_user_id, second_user_id])
    ).all()
    facility_by_user_id = {user_id: facility_id for user_id, facility_id in users}
    first_facility_id = facility_by_user_id.get(first_user_id)
    second_facility_id = facility_by_user_id.get(second_user_id)
    if first_facility_id is None or second_facility_id is None:
        return True
    return first_facility_id == second_facility_id
