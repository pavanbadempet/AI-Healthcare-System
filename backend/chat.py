"""Chat and Records API"""
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import agent, audit, auth, database, models, pdf_generator, rag, schemas

logger = logging.getLogger(__name__)
router = APIRouter()
HEALTH_REPORT_FAILURE_DETAIL = "Failed to generate health report"
CHAT_MEDICAL_DISCLAIMER = (
    "This is AI-generated information and is not a medical diagnosis. "
    "Please consult a qualified healthcare professional for medical decisions or emergencies."
)

# Maximum input lengths to prevent abuse
MAX_CHAT_MESSAGE_LENGTH = 4000
MAX_RECORD_TYPE_LENGTH = 50


def _sanitize_chat_input(message: str) -> str:
    """Sanitize chat input: strip, limit length, reject obviously malicious content."""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    sanitized = message.strip()
    if len(sanitized) > MAX_CHAT_MESSAGE_LENGTH:
        raise HTTPException(status_code=400, detail=f"Message exceeds maximum length of {MAX_CHAT_MESSAGE_LENGTH} characters")
    # Reject null bytes and control characters (except newline/tab)
    if '\x00' in sanitized or any(ord(c) < 32 and c not in ('\n', '\t') for c in sanitized):
        raise HTTPException(status_code=400, detail="Message contains invalid characters")
    return sanitized


def _sanitize_record_type(record_type: str) -> str:
    """Validate record type against allowed values."""
    if not record_type or not record_type.strip():
        raise HTTPException(status_code=400, detail="Record type cannot be empty")
    sanitized = record_type.strip().lower()
    if len(sanitized) > MAX_RECORD_TYPE_LENGTH:
        raise HTTPException(status_code=400, detail="Record type too long")
    return sanitized


def _with_medical_disclaimer(response: str) -> str:
    if CHAT_MEDICAL_DISCLAIMER in response:
        return response
    return f"{response}\n\n{CHAT_MEDICAL_DISCLAIMER}"

# --- Schemas ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    current_context: Dict[str, Any] = {}

class RecordCreate(BaseModel):
    record_type: str
    data: Dict[str, Any]
    prediction: str


# --- Chat Endpoints ---

@router.delete("/chat/history")
def delete_chat_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    deleted_count = db.query(models.ChatLog).filter(models.ChatLog.user_id == current_user.id).delete()
    db.commit()
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
        action="DELETE_CHAT_HISTORY",
        details={"resource_type": "chat_history", "deleted_count": deleted_count},
    )
    return {"status": "success"}

@router.get("/chat/history")
def get_chat_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = db.query(models.ChatLog).filter(models.ChatLog.user_id == current_user.id)\
        .order_by(models.ChatLog.timestamp.desc()).limit(100).all()
    logs.reverse()
    return [{"role": log.role, "content": log.content, "timestamp": log.timestamp} for log in logs]

@router.post("/chat")
def chat_endpoint(request: ChatRequest, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """AI Chat with RAG context."""
    sanitized_message = _sanitize_chat_input(request.message)
    save_data = bool(current_user.allow_data_collection)

    # Build profile
    profile = f"Name: {current_user.full_name or 'N/A'}, Age: {current_user.dob or 'N/A'}, " \
              f"Gender: {current_user.gender or 'N/A'}, Height/Weight: {current_user.height}/{current_user.weight}"

    # Save user message
    if save_data:
        try:
            log = models.ChatLog(user_id=current_user.id, role="user", content=sanitized_message)
            db.add(log)
            db.commit()
        except Exception:
            logger.error("Failed to save chat message")

    # Build message history
    messages = [HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
                for m in request.history]
    messages.append(HumanMessage(content=sanitized_message))

    # Get medical context
    context = ""
    if request.current_context:
        context = "\n".join([f"{k}: {v.get('prediction', 'N/A')}" for k, v in request.current_context.items() if isinstance(v, dict)])

    records = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id)\
        .order_by(models.HealthRecord.timestamp.desc()).limit(10).all()
    if records:
        context += "\nHistory: " + ", ".join([f"{r.record_type}:{r.prediction}" for r in records[:5]])

    # RAG memory
    rag_context = ""
    try:
        memories = rag.search_similar_records(str(current_user.id), sanitized_message, n_results=5)
        if memories:
            rag_context = "\n".join(memories[:3])
    except (ValueError, RuntimeError):
        pass

    # Invoke agent
    try:
        result = agent.medical_agent.invoke({
            "messages": messages,
            "user_profile": profile,
            "user_id": current_user.id,
            "available_reports": context,
            "rag_memories": rag_context,
            "conversation_count": len(messages)
        })
        response = _with_medical_disclaimer(result['messages'][-1].content)

        # Save AI response
        if save_data:
            try:
                db.add(models.ChatLog(user_id=current_user.id, role="assistant", content=response))
                db.commit()
            except Exception:
                logger.error("Failed to save chat response")

        return {"response": response}

    except Exception:
        logger.error("Agent error while processing chat request")
        return {"response": "Sorry, I'm having trouble right now. Please try again."}


# --- Record Endpoints ---

@router.post("/records")
def save_health_record(record: RecordCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    record_type = _sanitize_record_type(record.record_type)
    db_record = models.HealthRecord(
        user_id=current_user.id,
        record_type=record_type,
        data=json.dumps(record.data),
        prediction=record.prediction
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
        action="CREATE_HEALTH_RECORD",
        details={
            "resource_type": "health_record",
            "resource_id": db_record.id,
        },
    )
    rag.add_checkup_to_db(str(current_user.id), str(db_record.id), record_type, record.data, record.prediction, str(db_record.timestamp))
    return {"status": "success"}

@router.get("/records", response_model=List[schemas.HealthRecordResponse])
def get_health_records(record_type: Optional[str] = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    query = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id)
    if record_type:
        query = query.filter(models.HealthRecord.record_type == record_type)
    return query.order_by(models.HealthRecord.timestamp.asc()).all()

@router.delete("/records/{record_id}")
def delete_health_record(record_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    record = db.query(models.HealthRecord).filter(models.HealthRecord.id == record_id, models.HealthRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(record)
    db.commit()
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
        action="DELETE_HEALTH_RECORD",
        details={
            "resource_type": "health_record",
            "resource_id": record_id,
        },
    )
    rag.delete_record_from_db(str(record_id))
    return {"status": "success"}


# --- PDF Report ---

@router.get("/download/health-report")
def download_health_report(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    try:
        records = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id)\
            .order_by(models.HealthRecord.timestamp.desc()).limit(50).all()

        records_list = [{"timestamp": r.timestamp, "record_type": r.record_type, "prediction": r.prediction} for r in records]

        pdf_bytes = pdf_generator.generate_health_report(
            user_name=current_user.full_name or current_user.username,
            user_profile={"height": current_user.height, "weight": current_user.weight, "blood_type": current_user.blood_type},
            health_records=records_list
        )
        audit.record_audit_event(
            db,
            actor_user_id=current_user.id,
            target_user_id=current_user.id,
            action="DOWNLOAD_HEALTH_REPORT",
            details={"resource_type": "health_report", "record_count": len(records_list)},
        )

        filename = "Health_Report.pdf"
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        raise
    except Exception:
        logger.error("Health report generation failed")
        raise HTTPException(status_code=500, detail=HEALTH_REPORT_FAILURE_DETAIL)
