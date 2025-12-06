from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models, auth

models.Base.metadata.create_all(bind=engine)

def reset_password():
    db = SessionLocal()
    username = "pavansofts"
    new_password = "Admin123!"
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        user.hashed_password = auth.get_password_hash(new_password)
        db.commit()
        print(f"Password for '{username}' updated successfully to '{new_password}'.")
    else:
        print(f"User '{username}' not found.")
    db.close()

if __name__ == "__main__":
    reset_password()
