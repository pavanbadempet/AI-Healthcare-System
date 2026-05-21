from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from . import database, models, auth, schemas
from .facility_scope import users_share_facility_context
from datetime import datetime

ACTIVE_APPOINTMENT_STATUSES = ("Scheduled", "Rescheduled")
DEFAULT_SPECIALIZATION = "General Physician"
PAST_APPOINTMENT_DETAIL = "Appointment time must be in the future"
DUPLICATE_APPOINTMENT_DETAIL = "Doctor already has an active appointment at that time"
APPOINTMENT_FACILITY_MISMATCH_DETAIL = "Appointment participants must belong to the same facility"
APPOINTMENT_FACILITY_ACCESS_DETAIL = "Appointment resource is outside the user's facility"

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def _parse_appointment_datetime(date: str, time: str) -> datetime:
    dt_str = f"{date} {time}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Invalid date/time format")


def _doctor_specialization(doctor: models.User) -> str:
    specialization = (doctor.specialization or "").strip()
    return specialization or DEFAULT_SPECIALIZATION


def _doctor_display_name(doctor: models.User) -> str:
    return doctor.full_name or doctor.username


def _resolve_appointment_facility_id(patient: models.User, doctor: models.User) -> int | None:
    return patient.facility_id or doctor.facility_id


def _ensure_future_slot(appointment_dt: datetime) -> None:
    if appointment_dt <= datetime.now():
        raise HTTPException(status_code=400, detail=PAST_APPOINTMENT_DETAIL)


def _ensure_doctor_slot_available(
    db: Session,
    doctor_id: int,
    appointment_dt: datetime,
    *,
    exclude_appointment_id: int | None = None,
) -> None:
    query = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.date_time == appointment_dt,
        models.Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
    )
    if exclude_appointment_id is not None:
        query = query.filter(models.Appointment.id != exclude_appointment_id)
    if query.first():
        raise HTTPException(status_code=409, detail=DUPLICATE_APPOINTMENT_DETAIL)


def _scope_appointments_to_admin_facility(query, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(models.Appointment.facility_id == current_user.facility_id)


def _ensure_admin_can_access_appointment(current_user: models.User, appointment: models.Appointment) -> None:
    if not auth.is_admin(current_user) or current_user.facility_id is None:
        return
    if appointment.facility_id != current_user.facility_id:
        raise HTTPException(status_code=403, detail=APPOINTMENT_FACILITY_ACCESS_DETAIL)


@router.post("/", response_model=schemas.AppointmentResponse)
def create_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Combine date and time strings into a datetime object
    dt_str = f"{appt.date} {appt.time}"
    appointment_dt = _parse_appointment_datetime(appt.date, appt.time)

    doctor = db.query(models.User).filter(
        models.User.id == appt.doctor_id,
        models.User.role == "doctor"
    ).first()
    if not doctor:
        raise HTTPException(status_code=400, detail="Selected doctor not found")
    if not users_share_facility_context(db, current_user.id, doctor.id):
        raise HTTPException(status_code=400, detail=APPOINTMENT_FACILITY_MISMATCH_DETAIL)
    specialization = _doctor_specialization(doctor)
    facility_id = _resolve_appointment_facility_id(current_user, doctor)
    _ensure_future_slot(appointment_dt)
    _ensure_doctor_slot_available(db, doctor.id, appointment_dt)
    
    new_appt = models.Appointment(
        facility_id=facility_id,
        user_id=current_user.id,
        doctor_id=doctor.id,
        specialist=specialization,
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
        doctor_name=_doctor_display_name(doctor),
        date_time=dt_str,
        link=video_link
    )
    
    return new_appt

@router.get("/", response_model=list[schemas.AppointmentResponse])
def get_appointments(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if auth.is_admin(current_user):
        query = _scope_appointments_to_admin_facility(db.query(models.Appointment), current_user)
        return query.order_by(models.Appointment.date_time.asc()).all()

    if current_user.role == "doctor":
        return db.query(models.Appointment).filter(
            models.Appointment.doctor_id == current_user.id
        ).order_by(models.Appointment.date_time.asc()).all()
        
    return db.query(models.Appointment).filter(
        models.Appointment.user_id == current_user.id
    ).order_by(models.Appointment.date_time.asc()).all()

@router.get("/doctors", response_model=list[schemas.DoctorResponse])
def get_doctors(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Fetch all users with role='doctor'"""
    query = db.query(models.User).filter(models.User.role == "doctor")
    if auth.is_admin(current_user) and current_user.facility_id is not None:
        query = query.filter(models.User.facility_id == current_user.facility_id)
    elif not auth.is_admin(current_user) and current_user.facility_id is not None:
        query = query.filter(
            or_(
                models.User.facility_id == current_user.facility_id,
                models.User.facility_id.is_(None),
            )
        )
    doctors = query.all()
    # Map to DoctorResponse (handling missing profile fields)
    response = []
    for doc in doctors:
        response.append(schemas.DoctorResponse(
            id=doc.id,
            full_name=doc.full_name or doc.username,
            specialization=_doctor_specialization(doc),
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
    _ensure_admin_can_access_appointment(current_user, appt)
        
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
    _ensure_admin_can_access_appointment(current_user, appt)
        
    if current_user.role != "admin" and appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_dt = _parse_appointment_datetime(date, time)
    _ensure_future_slot(new_dt)
    if appt.doctor_id is not None:
        _ensure_doctor_slot_available(
            db,
            appt.doctor_id,
            new_dt,
            exclude_appointment_id=appt.id,
        )
    
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
    _ensure_admin_can_access_appointment(current_user, appt)
        
    if current_user.role != "admin" and appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(appt)
    db.commit()
    return {"message": "Appointment deleted"}
