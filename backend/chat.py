from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from . import models, database, auth, rag, agent
import json
import datetime

router = APIRouter()

# --- Sync Data on Startup (Optional, but good for local dev) ---
def sync_data_to_chroma(db: Session):
    """Indexes all existing records into Chroma if not present."""
    records = db.query(models.HealthRecord).all()
    # In a real app, we check if indexed. For now, we trust RAG to handle updates or re-index.
    # We will just simple add them. rag.add_checkup_to_db handles idempotency if we use record_id as ID.
    for rec in records:
        try:
            data_dict = json.loads(rec.data)
        except:
            data_dict = {}
        rag.add_checkup_to_db(
            record_id=str(rec.id),
            record_type=rec.record_type,
            data=data_dict,
            prediction=rec.prediction,
            timestamp=str(rec.timestamp)
        )

# --- Chat Endpoint with LangGraph Agent ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []

@router.delete("/chat/history")
def delete_chat_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.query(models.ChatLog).filter(models.ChatLog.user_id == current_user.id).delete()
    db.commit()
    return {"status": "success", "message": "Chat history cleared"}

@router.get("/chat/history")
def get_chat_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = db.query(models.ChatLog).filter(models.ChatLog.user_id == current_user.id).order_by(models.ChatLog.timestamp).all()
    return [{"role": log.role, "content": log.content, "timestamp": log.timestamp} for log in logs]

@router.post("/chat")
def chat_endpoint(request: ChatRequest, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
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

    # Save User Message (SQL + RAG)
    if save_data:
        try:
            # SQL
            user_log = models.ChatLog(user_id=current_user.id, role="user", content=request.message, timestamp=datetime.datetime.utcnow())
            db.add(user_log)
            db.commit()
            db.refresh(user_log)
            
            # RAG
            rag.add_interaction_to_db(str(user_log.id), "user", request.message, str(user_log.timestamp))
        except Exception as e:
            print(f"Error saving user log: {e}")

    # 2. Convert History to LangChain Messages
    graph_messages = []
    # Fetch recent history from DB if we want true robust history, or rely on frontend?
    # Hybrid: Frontend sends visible history, we trust it for context. 
    # Logic remains same for context building.
    for msg in request.history:
        if msg.role == "user":
            graph_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            graph_messages.append(AIMessage(content=msg.content))
    
    graph_messages.append(HumanMessage(content=request.message))

    # 2.5 Fetch Available Records for Truthfulness & Deep Context (Timeline)
    # Fetch ALL records for user, sorted by timestamp DESC
    all_records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.timestamp.desc()).all()
    
    # Group by Type and take top 5
    from collections import defaultdict
    import json
    
    records_by_type = defaultdict(list)
    for rec in all_records:
        # Validate Data Integrity
        try:
            d = json.loads(rec.data)
            # Filter Logic: Reject if key vitals are 0
            is_valid = True
            if rec.record_type == "Diabetes":
                if float(d.get("glucose", 0)) < 10 or float(d.get("bmi", 0)) < 5: is_valid = False
            elif rec.record_type == "Heart Disease":
                if float(d.get("trestbps", 0)) < 10 or float(d.get("chol", 0)) < 10: is_valid = False
            elif rec.record_type == "Liver Disease":
                if float(d.get("total_bilirubin", 0)) == 0: is_valid = False
            
            if is_valid:
                records_by_type[rec.record_type].append(rec)
        except:
            pass # Skip malformed JSON
    
    if records_by_type:
        summary_lines = []
        for r_type, recs in records_by_type.items():
            # Take top 5 recent
            top_5 = recs[:5]
            # Sort chronologically for the AI to read naturally (Oldest -> Newest)
            top_5_asc = sorted(top_5, key=lambda x: x.timestamp)
            
            summary_lines.append(f"--- {r_type} History ---")
            for r in top_5_asc:
                summary_lines.append(f"- {r.timestamp.strftime('%Y-%m-%d')}: {r.prediction}")
                
        available_reports_str = "\n".join(summary_lines)
    else:
        available_reports_str = "No prior health records found."

    # 3. Invoke Agent
    try:
        inputs = {
            "messages": graph_messages,
            "user_profile": profile_str,
            "available_reports": available_reports_str
        }
        
        # Invoke the graph
        result = agent.medical_agent.invoke(inputs)
        
        # Extract response
        last_msg = result['messages'][-1]
        response_text = last_msg.content
        
        # Save AI Response (SQL + RAG)
        if save_data:
            try:
                # SQL
                ai_log = models.ChatLog(user_id=current_user.id, role="assistant", content=response_text, timestamp=datetime.datetime.utcnow())
                db.add(ai_log)
                db.commit()
                db.refresh(ai_log)
                
                # RAG
                rag.add_interaction_to_db(str(ai_log.id), "assistant", response_text, str(ai_log.timestamp))
            except Exception as e:
                print(f"Error saving AI log: {e}")

        return {"response": response_text}

    except Exception as e:
        print(f"AGENT ERROR: {e}")
        return {"response": "I'm having trouble analyzing your files right now.", "error": str(e)}

# --- Record Management with Vector DB Sync ---

class RecordCreate(BaseModel):
    record_type: str
    data: dict
    prediction: str

@router.post("/records")
def save_health_record(record: RecordCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_record = models.HealthRecord(
        user_id=current_user.id,
        record_type=record.record_type,
        data=json.dumps(record.data),
        prediction=record.prediction
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Sync to Chroma
    rag.add_checkup_to_db(
        record_id=str(db_record.id),
        record_type=db_record.record_type,
        data=record.data,
        prediction=db_record.prediction,
        timestamp=str(db_record.timestamp)
    )
    
    return {"status": "success", "message": "Health record saved."}

@router.get("/records")
def get_health_records(record_type: str = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    query = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id)
    if record_type:
        query = query.filter(models.HealthRecord.record_type == record_type)
    return query.order_by(models.HealthRecord.timestamp.asc()).all()  # ASC for graphing

@router.delete("/records/{record_id}")
def delete_health_record(record_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    record = db.query(models.HealthRecord).filter(models.HealthRecord.id == record_id, models.HealthRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Delete from DB
    db.delete(record)
    db.commit()
    
    # Delete from Chroma
    rag.delete_record_from_db(str(record_id))
    
    return {"status": "success", "message": "Record deleted"}
