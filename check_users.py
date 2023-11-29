from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models

models.Base.metadata.create_all(bind=engine)

def list_users():
    db = SessionLocal()
    users = db.query(models.User).all()
    print(f"Total Users: {len(users)}")
    for u in users:
        print(f"- ID: {u.id} | Username: {u.username} | Email: {u.email}")
    db.close()

if __name__ == "__main__":
    list_users()
