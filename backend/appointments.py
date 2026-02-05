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
        doctor_id=appt.doctor_id,
        specialist=appt.specialist,
        date_time=appointment_dt,
        reason=appt.reason,
        status="Scheduled"
    )
    
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    
    # Send Confirmation Email (Async/Background in production, Sync here for safety)
    from . import email_service
    video_link = f"https://meet.jit.si/ai-health-{new_appt.id}" # Secure unique link
    
    email_service.send_booking_confirmation(
        to_email=current_user.email or "patient@example.com",
        patient_name=current_user.full_name or current_user.username,
        doctor_name=appt.specialist,
        date_time=dt_str,
        link=video_link
    )
    
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

@router.get("/doctors", response_model=list[schemas.DoctorResponse])
def get_doctors(db: Session = Depends(database.get_db)):
    """Fetch all users with role='doctor'"""
    doctors = db.query(models.User).filter(models.User.role == "doctor").all()
    # Map to DoctorResponse (handling missing profile fields)
    response = []
    for doc in doctors:
        response.append(schemas.DoctorResponse(
            id=doc.id,
            full_name=doc.full_name or doc.username,
            specialization="General Physician", # Hardcoded for now or fetch from profile if stored
            consultation_fee=doc.consultation_fee or 500.0,
            profile_picture=doc.profile_picture
        ))
    return response
@router.put("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Permission check
    if current_user.role != "admin" and appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    appt.status = "Cancelled"
    db.commit()
    return {"message": "Appointment cancelled"}

@router.put("/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int,
    date: str, # Expecting YYYY-MM-DD
    time: str, # Expecting HH:MM:SS or HH:MM
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.role != "admin" and appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Combine date and time
    try:
        dt_str = f"{date} {time}"
        new_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
             new_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except:
             raise HTTPException(status_code=400, detail="Invalid date/time format")
    
    appt.date_time = new_dt
    appt.status = "Rescheduled"
    db.commit()
    return {"message": "Appointment rescheduled"}

@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Admin or Owner can delete an appointment."""
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.role != "admin" and appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(appt)
    db.commit()
    return {"message": "Appointment deleted"}
