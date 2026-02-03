"""
Admin Dashboard Logic
=====================
Endpoints for system administration, analytics, and user management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import database, models, auth
from typing import List, Dict

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# --- Dependencies ---

def get_current_admin(current_user: models.User = Depends(auth.get_current_user)):
    """
    Dependency to ensure the user is an Admin.
    For this MVP, we'll hardcode 'admin' username as the superuser, 
    or check a role column if we added one. 
    Let's check if username is 'admin' or starts with 'admin_'.
    """
    if not (current_user.username == "admin" or current_user.username.startswith("admin_")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# --- Endpoints ---

@router.get("/stats")
def get_system_stats(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Get high-level system statistics."""
    total_users = db.query(models.User).count()
    total_records = db.query(models.HealthRecord).count()
    total_chats = db.query(models.ChatLog).count()
    
    # Calculate mock revenue based on "Pro" users (future)
    # For now, just return 0
    
    return {
        "total_users": total_users,
        "total_predictions": total_records,
        "total_messages": total_chats,
        "server_status": "Healthy",
        "database_status": "Connected"
    }

@router.get("/users")
def get_recent_users(
    skip: int = 0, 
    limit: int = 20,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
):
    """List recent users for management."""
    users = db.query(models.User).order_by(models.User.id.desc()).offset(skip).limit(limit).all()
    # Sanitize passwords
    safe_users = []
    for u in users:
        safe_users.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "joined": u.created_at.strftime("%Y-%m-%d") if u.created_at else "2024-01-01"
        })
    return safe_users
