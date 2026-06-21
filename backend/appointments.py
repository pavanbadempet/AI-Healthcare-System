import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import audit, auth, core_ai, database, email_service, models, schemas
from .agents.scheduling_agent import BOOKING_ACTION_PATTERN, SchedulingAgent
from .facility_scope import users_share_facility_context

ACTIVE_APPOINTMENT_STATUSES = ("Scheduled", "Rescheduled")
DEFAULT_SPECIALIZATION = "General Physician"
PAST_APPOINTMENT_DETAIL = "Appointment time must be in the future"
DUPLICATE_APPOINTMENT_DETAIL = "Doctor already has an active appointment at that time"
APPOINTMENT_FACILITY_MISMATCH_DETAIL = "Appointment participants must belong to the same facility"
APPOINTMENT_FACILITY_ACCESS_DETAIL = "Appointment resource is outside the user's facility"
logger = logging.getLogger(__name__)

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
    facility_id = current_user.facility_id or "global"
    is_admin_user = auth.is_admin(current_user)
    cache_key = f"doctors:{facility_id}:{is_admin_user}"

    from .cache_service import cache
    try:
        cached_res = cache.get(cache_key)
        if cached_res is not None:
            return cached_res
    except Exception as ex_cache:
        logger.debug("Doctor list cache lookup failed: %s", ex_cache)

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

    try:
        # Cache for 10 seconds to absorb page load bursts
        cache.set(cache_key, response, ttl=10)
    except Exception as ex_cache:
        logger.debug("Doctor list cache set failed: %s", ex_cache)

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


# --- CASA Agentic Scheduling Endpoints ---

class CASAMessage(BaseModel):
    role: str
    content: str

class CASAChatRequest(BaseModel):
    message: str
    history: List[CASAMessage] = []

@router.post("/agent-chat")
async def agent_chat_endpoint(
    req: CASAChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Conversational appointment scheduling chat endpoint."""
    agent = SchedulingAgent(db, current_user)
    history_list = [{"role": h.role, "content": h.content} for h in req.history]
    result = await agent.chat(req.message, history_list)
    return result

@router.post("/agent-stream")
async def agent_stream_endpoint(
    req: CASAChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Streaming conversational appointment scheduling chat endpoint."""
    agent = SchedulingAgent(db, current_user)

    # Pre-check symptoms
    warning, _ = agent._check_symptoms(req.message)
    system_prompt = agent.get_system_prompt()

    # Format history for LLM chat stream
    chat_history = [{"role": h.role, "content": h.content} for h in req.history]
    chat_history.append({"role": "user", "content": req.message})

    async def stream_generator():
        last_activity = time.time()
        streamed_reply_parts = []
        stream_task = None

        try:
            # 1. Send warning immediately if exists
            if warning:
                yield f"data: {json.dumps({'reply': warning + '\n\n', 'status': 'warning'})}\n\n"
                streamed_reply_parts.append(warning + "\n\n")

            # 2. Setup AI stream
            chunk_queue = asyncio.Queue()

            async def ai_stream_consumer():
                try:
                    async for chunk in core_ai.chat_stream(
                        chat_history,
                        system=system_prompt
                    ):
                        if chunk:
                            await chunk_queue.put(("chunk", chunk))
                    await chunk_queue.put(("done", None))
                except Exception as ex:
                    await chunk_queue.put(("error", str(ex)))

            stream_task = asyncio.create_task(ai_stream_consumer())

            while True:
                try:
                    msg_type, data = await asyncio.wait_for(
                        chunk_queue.get(),
                        timeout=15.0
                    )

                    if msg_type == "chunk":
                        streamed_reply_parts.append(data)
                        yield f"data: {json.dumps({'reply': data})}\n\n"
                        last_activity = time.time()
                    elif msg_type == "error":
                        yield f"data: {json.dumps({'error': data, 'status': 'error'})}\n\n"
                        break
                    elif msg_type == "done":
                        full_reply = "".join(streamed_reply_parts)

                        # Check booking tag in background
                        booking_match = BOOKING_ACTION_PATTERN.search(full_reply)
                        booking_details = None
                        error_msg = None

                        if booking_match:
                            doc_id_str, date_str, time_str, reason_str = booking_match.groups()
                            try:
                                doc_id = int(doc_id_str)
                                dt_str = f"{date_str} {time_str}"
                                appointment_dt = None
                                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                                    try:
                                        appointment_dt = datetime.strptime(dt_str, fmt)
                                        break
                                    except ValueError:
                                        continue
                                if not appointment_dt or appointment_dt <= datetime.now():
                                    raise ValueError("Invalid date/time or time is in the past")

                                doctor = db.query(models.User).filter(
                                    models.User.id == doc_id,
                                    models.User.role == "doctor"
                                ).first()
                                if not doctor:
                                    raise ValueError(f"Doctor with ID {doc_id} not found")

                                if not users_share_facility_context(db, current_user.id, doctor.id):
                                    raise ValueError("Doctor does not belong to facility scope")

                                existing = db.query(models.Appointment).filter(
                                    models.Appointment.doctor_id == doc_id,
                                    models.Appointment.date_time == appointment_dt,
                                    models.Appointment.status.in_(("Scheduled", "Rescheduled"))
                                ).first()
                                if existing:
                                    raise ValueError("Doctor already booked at that slot")

                                # Run pre-screening
                                spec = doctor.specialization or "General Physician"
                                screen_res = agent._run_clinical_screening(spec)
                                final_reason = reason_str.strip()
                                if screen_res:
                                    brief = f"[AI Risk Screen: {screen_res['model_name'].title()} {screen_res['risk_level']} Risk ({screen_res['confidence']}%)]"
                                    final_reason = f"{brief} {final_reason}"

                                new_appt = models.Appointment(
                                    facility_id=doctor.facility_id or current_user.facility_id,
                                    user_id=current_user.id,
                                    doctor_id=doctor.id,
                                    specialist=spec,
                                    date_time=appointment_dt,
                                    reason=final_reason,
                                    status="Scheduled"
                                )
                                db.add(new_appt)

                                if screen_res:
                                    db_record = models.HealthRecord(
                                        user_id=current_user.id,
                                        record_type=screen_res["model_name"],
                                        data=json.dumps(screen_res.get("input_data", {})),
                                        prediction=f"{screen_res['risk_level']} Risk ({screen_res['confidence']}%)"
                                    )
                                    db.add(db_record)

                                db.commit()
                                db.refresh(new_appt)

                                try:
                                    video_link = f"https://meet.jit.si/ai-health-{new_appt.id}"
                                    email_service.send_booking_confirmation(
                                        to_email=current_user.email or "patient@example.com",
                                        patient_name=current_user.full_name or current_user.username,
                                        doctor_name=doctor.full_name or doctor.username,
                                        date_time=dt_str,
                                        link=video_link
                                    )
                                except Exception:
                                    logger.warning("Failed to send email confirmation")

                                booking_details = {
                                    "id": new_appt.id,
                                    "doctor_name": doctor.full_name or doctor.username,
                                    "specialist": doctor.specialization or "General Physician",
                                    "date_time": new_appt.date_time.isoformat(),
                                    "reason": new_appt.reason
                                }
                                yield f"data: {json.dumps({'action_triggered': True, 'booking_details': booking_details, 'status': 'complete'})}\n\n"
                            except Exception as ex:
                                db.rollback()
                                error_msg = str(ex)
                                yield f"data: {json.dumps({'action_triggered': True, 'error': error_msg, 'status': 'complete'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'action_triggered': False, 'status': 'complete'})}\n\n"
                        break
                except asyncio.TimeoutError:
                    if time.time() - last_activity >= 15.0:
                        yield ":heartbeat (keepalive)\n\n"
                        last_activity = time.time()
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        finally:
            if stream_task and not stream_task.done():
                stream_task.cancel()

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# --- Phase 10 Itch Upgrades: Special Appointments and Referral Matching ---
from pydantic import BaseModel as PydanticBaseModel


class SpecialCareBookingRequest(PydanticBaseModel):
    patient_id: int
    doctor_id: int | None = None
    specialist: str
    date_time: str
    reason: str
    request_female_clinician: bool = False
    home_visit_van: bool = False


@router.post("/special-care")
def book_special_care_appointment(
    req: SpecialCareBookingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role == "patient" and current_user.id != req.patient_id:
        raise HTTPException(status_code=403, detail="Patients can only book for themselves")

    from datetime import datetime
    try:
        parsed_dt = datetime.fromisoformat(req.date_time)
    except Exception:
        parsed_dt = datetime.now(timezone.utc)

    notes = f"Special Care Preference: Female clinician requested: {req.request_female_clinician}. Home visit van: {req.home_visit_van}."
    final_reason = f"[Special Care: {'Female Staff Requested' if req.request_female_clinician else 'Standard Staff'}, {'Mobile Van Visit' if req.home_visit_van else 'In-clinic Visit'}] {req.reason}"

    db_appt = models.Appointment(
        facility_id=current_user.facility_id or 1,
        user_id=req.patient_id,
        doctor_id=req.doctor_id,
        specialist=req.specialist,
        date_time=parsed_dt,
        reason=final_reason,
        status="Scheduled"
    )
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)

    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=req.patient_id,
        action="BOOK_SPECIAL_CARE_APPOINTMENT",
        details={"appointment_id": db_appt.id, "female_clinician": req.request_female_clinician, "home_visit": req.home_visit_van}
    )

    return {
        "appointment_id": db_appt.id,
        "patient_id": req.patient_id,
        "specialist": req.specialist,
        "date_time": db_appt.date_time.isoformat(),
        "female_clinician_assigned": req.request_female_clinician,
        "home_visit_arranged": req.home_visit_van,
        "status": "Scheduled",
        "notes": notes,
        "message": "Successfully scheduled specialized private mobile diagnostic consultation."
    }


@router.get("/recommend-specialists/{patient_id}")
def recommend_specialists_based_on_risks(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Patients can only check their own specialist recommendations")

    recent_records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == patient_id
    ).order_by(models.HealthRecord.timestamp.desc()).all()

    predictions_summary = {}
    for r in recent_records:
        if r.record_type not in predictions_summary:
            predictions_summary[r.record_type] = r.prediction

    recommendations = []

    for model, prediction in predictions_summary.items():
        if "high" in prediction.lower() or "danger" in prediction.lower():
            if model == "heart":
                recommendations.append({
                    "specialty": "Cardiology",
                    "reason": f"Recommended due to High Heart Disease risk prediction ({prediction}).",
                    "priority": "High"
                })
            elif model == "diabetes":
                recommendations.append({
                    "specialty": "Endocrinology",
                    "reason": f"Recommended due to High Diabetes risk prediction ({prediction}).",
                    "priority": "High"
                })
            elif model == "kidney":
                recommendations.append({
                    "specialty": "Nephrology",
                    "reason": f"Recommended due to High Kidney Disease risk prediction ({prediction}).",
                    "priority": "High"
                })
            elif model == "liver":
                recommendations.append({
                    "specialty": "Hepatology / Gastroenterology",
                    "reason": f"Recommended due to High Liver Disease risk prediction ({prediction}).",
                    "priority": "High"
                })
            elif model == "lungs":
                recommendations.append({
                    "specialty": "Pulmonology",
                    "reason": f"Recommended due to High Lung Cancer risk prediction ({prediction}).",
                    "priority": "High"
                })

    if not recommendations:
        recommendations.append({
            "specialty": "General Medicine",
            "reason": "All ML disease risk profiles are low; standard periodic wellness check recommended.",
            "priority": "Routine"
        })

    return {
        "patient_id": patient_id,
        "recommended_specialties": recommendations,
        "total_recommendations": len(recommendations),
        "clinical_safety_note": "Specialist referral matching is an automated diagnostic decision-support aid. Clinicians review and confirm all referrals."
    }
