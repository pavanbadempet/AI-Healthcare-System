from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from . import models, database, auth, rag, agent
import json

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
        f"Known Ailments: {current_user.existing_ailments or 'None'}"
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

    # 2.5 Fetch Available Records for Truthfulness
    available_records = db.query(models.HealthRecord.record_type).filter(models.HealthRecord.user_id == current_user.id).distinct().all()
    # available_records is a list of tuples like [('Diabetes',), ('Heart',)]
    record_list = [rec[0] for rec in available_records]
    available_reports_str = ", ".join(record_list) if record_list else "None"

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
def get_health_records(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    records = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == current_user.id).order_by(models.HealthRecord.timestamp.desc()).all()
    return records

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
