from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import database, models, auth, schemas
from datetime import datetime

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

@router.post("/", response_model=schemas.AppointmentResponse)
def create_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Combine date and time strings into a datetime object
    try:
        dt_str = f"{appt.date} {appt.time}"
        appointment_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
             # Try without seconds if failed
             appointment_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except:
             raise HTTPException(status_code=400, detail="Invalid date/time format")
    
    new_appt = models.Appointment(
        user_id=current_user.id,
        specialist=appt.specialist,
        date_time=appointment_dt,
        reason=appt.reason,
        status="Scheduled"
    )
    
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    return new_appt

@router.get("/", response_model=list[schemas.AppointmentResponse])
def get_appointments(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role in ["admin", "doctor"]:
        return db.query(models.Appointment).order_by(models.Appointment.date_time.asc()).all()
        
    return db.query(models.Appointment).filter(
        models.Appointment.user_id == current_user.id
    ).order_by(models.Appointment.date_time.asc()).all()
