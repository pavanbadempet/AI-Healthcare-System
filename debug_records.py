from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models

def check_records():
    db = SessionLocal()
    # Get user pavansofts
    user = db.query(models.User).filter(models.User.username == "pavansofts").first()
    if not user:
        print("User pavansofts not found!")
        return

    print(f"Checking records for User: {user.username} (ID: {user.id})")
    records = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == user.id).all()
    
    if not records:
        print("NO RECORDS FOUND.")
    else:
        print(f"Found {len(records)} records:")
        for r in records:
            print(f"- [{r.timestamp}] Type: {r.record_type} | Pred: {r.prediction} | Data: {r.data}")

    db.close()

if __name__ == "__main__":
    check_records()
