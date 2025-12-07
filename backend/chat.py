from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from . import models, database, auth, rag, agent
import json
import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

# --- Router Definition ---
router = APIRouter()

# --- Schemas ---

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    """Schema for incoming chat messages."""
    message: str
    history: List[Message] = []

class RecordCreate(BaseModel):
    """Schema for saving a health record."""
    record_type: str
    data: Dict[str, Any]
    prediction: str

# --- Endpoints ---

@router.delete("/chat/history")
def delete_chat_history(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> Dict[str, str]:
    """
    Clear all chat history for the current user.
    """
    db.query(models.ChatLog).filter(models.ChatLog.user_id == current_user.id).delete()
    db.commit()
    return {"status": "success", "message": "Chat history cleared"}

@router.get("/chat/history", response_model=List[Dict[str, Any]])
def get_chat_history(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> List[Dict[str, Any]]:
    """
    Retrieve past chat interactions for the timeline UI.
    
    Returns:
        List of dicts: [{"role": "user", "content": "..."}]
    """
    LOG_LIMIT = 100
    logs = db.query(models.ChatLog).filter(
        models.ChatLog.user_id == current_user.id
    ).order_by(models.ChatLog.timestamp.desc()).limit(LOG_LIMIT).all()
    
    # Reverse to show oldest first in UI
    logs.reverse()
    
    return [{"role": log.role, "content": log.content, "timestamp": log.timestamp} for log in logs]

@router.post("/chat")
def chat_endpoint(
    request: ChatRequest, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """
    Core AI Chat Endpoint.
    Orchestrates: Intent -> RAG -> Agent -> Memory.
    """
    # 0. Check Privacy Setting
    save_data = bool(current_user.allow_data_collection)

    # 1. Build User Profile String
    profile_str = (
        f"Name: {current_user.full_name or 'N/A'}\n"
        f"Age/DOB: {current_user.dob or 'N/A'}\n"
        f"Gender: {current_user.gender or 'N/A'}\n"
        f"Height: {current_user.height}cm, Weight: {current_user.weight}kg\n"
        f"Blood Type: {current_user.blood_type or 'N/A'}\n"
        f"Known Ailments: {current_user.existing_ailments or 'None'}\n"
        f"Diet: {current_user.diet or 'Unspecified'}\n"
        f"Activity: {current_user.activity_level or 'Unspecified'}\n"
        f"Sleep: {current_user.sleep_hours or '?'} hours/night\n"
        f"Stress: {current_user.stress_level or 'Unspecified'}\n"
        f"About Me: {current_user.about_me or 'None'}"
    )

    # Save User Message to DB
    if save_data:
        try:
            user_log = models.ChatLog(user_id=current_user.id, role="user", content=request.message, timestamp=datetime.datetime.utcnow())
            db.add(user_log)
            db.commit()
            db.refresh(user_log)
            rag.add_interaction_to_db(str(current_user.id), str(user_log.id), "user", request.message, str(user_log.timestamp))
        except Exception as e:
            print(f"Error saving user log: {e}")

    # 2. Build Agent Graph Context
    graph_messages = []
    for msg in request.history:
        if msg.role == "user":
            graph_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            graph_messages.append(AIMessage(content=msg.content))
    graph_messages.append(HumanMessage(content=request.message))

    # 3. Build Medical Context (Real-time + History)
    context_str = ""
    
    # A. Real-time Context (From Session State passed via API)
    if request.current_context:
        context_str += "--- CURRENT SESSION RESULTS ---\n"
        for k, v in request.current_context.items():
            if isinstance(v, dict) and "prediction" in v:
                pred = v["prediction"]
                context_str += f"- {k}: {pred}\n"
    
    # B. Historical Context (From DB) - Optimised to last 50 records
    all_records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.timestamp.desc()).limit(50).all()
    
    if all_records:
        context_str += "\n--- MEDICAL HISTORY ---\n"
        records_by_type = defaultdict(list)
        for rec in all_records:
            records_by_type[rec.record_type].append(rec)
            
        for r_type, recs in records_by_type.items():
            top_3 = recs[:3] # Latest 3
            for r in top_3:
                 context_str += f"- {r.timestamp.strftime('%Y-%m-%d')}: {r.record_type} -> {r.prediction}\n"

    if not context_str:
        context_str = "No prior health records found."

    # 4. Invoke Agent
    try:
        inputs = {
            "messages": graph_messages,
            "user_profile": profile_str,
            "user_id": current_user.id, # Used by tools for RAG lookup
            "available_reports": context_str # Injected into Prompt
        }
        
        result = agent.medical_agent.invoke(inputs)
        
        last_msg = result['messages'][-1]
        response_text = last_msg.content
        
        # Save AI Response
        if save_data:
            try:
                ai_log = models.ChatLog(user_id=current_user.id, role="assistant", content=response_text, timestamp=datetime.datetime.utcnow())
                db.add(ai_log)
                db.commit()
                db.refresh(ai_log)
                rag.add_interaction_to_db(str(current_user.id), str(ai_log.id), "assistant", response_text, str(ai_log.timestamp))
            except Exception as e:
                print(f"Error saving AI log: {e}")

        return {"response": response_text}

    except Exception as e:
        print(f"AGENT ERROR: {e}")
        return {"response": "I'm having trouble analyzing your files right now. Please try again later.", "error": str(e)}

# --- Record Management Endpoints ---

@router.post("/records")
def save_health_record(
    record: RecordCreate, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> Dict[str, str]:
    """
    Save a prediction result (Diabetes/Heart/Liver) to DB and Vector Index.
    """
    db_record = models.HealthRecord(
        user_id=current_user.id,
        record_type=record.record_type,
        data=json.dumps(record.data),
        prediction=record.prediction
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Sync to Chroma/RAG
    rag.add_checkup_to_db(
        user_id=str(current_user.id),
        record_id=str(db_record.id),
        record_type=db_record.record_type,
        data=record.data,
        prediction=db_record.prediction,
        timestamp=str(db_record.timestamp)
    )
    
    return {"status": "success", "message": "Health record saved."}

@router.get("/records")
def get_health_records(
    record_type: Optional[str] = None, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> List[Any]:
    """Retrieve health records, optionally filtered by type."""
    query = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id)
    if record_type:
        query = query.filter(models.HealthRecord.record_type == record_type)
    return query.order_by(models.HealthRecord.timestamp.asc()).all()

@router.delete("/records/{record_id}")
def delete_health_record(
    record_id: int, 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
) -> Dict[str, str]:
    """
    Delete a health record permanently from SQL and Vector Store.
    """
    record = db.query(models.HealthRecord).filter(models.HealthRecord.id == record_id, models.HealthRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # SQL Delete
    db.delete(record)
    db.commit()
    
    # Vector Delete
    rag.delete_record_from_db(str(record_id))
    
    return {"status": "success", "message": "Record deleted"}
