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
def get_admin_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> Dict:
    """Get high-level system statistics."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate mock revenue based on "Pro" users (future)
    # For now, just return 0
    
    return {
        "total_users": db.query(models.User).count(),
        "total_predictions": db.query(models.HealthRecord).count(),
        "total_messages": db.query(models.ChatLog).count(),
        "server_status": "Online",
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
    return safe_users

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int, 
    role: str,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Update a user's system role (patient, doctor, admin)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if role not in ["patient", "doctor", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be patient, doctor, or admin.")
        
    user.role = role
    db.commit()
    return {"status": "success", "message": f"User {user.username} promoted to {role}"}
