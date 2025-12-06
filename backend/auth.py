from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models, database
from sqlalchemy.exc import IntegrityError

import os
import re
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-dev-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    dob: str # YYYY-MM-DD

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    class Config:
        from_attributes = True

# Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# Endpoints
@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(database.get_db)):
    try:
        # Password Complexity Check
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$", user.password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters and contain both letters and numbers."
            )

        # Check Username
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check Email (Optional but good practice)
        if user.email:
             db_email = db.query(models.User).filter(models.User.email == user.email).first()
             if db_email:
                 raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_password_hash(user.password)
        
        new_user = models.User(
            username=user.username, 
            hashed_password=hashed_password,
            email=user.email,
            full_name=user.full_name,
            dob=user.dob,
            existing_ailments="",
            profile_picture="",
            allow_data_collection=1
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or Email already registered.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Signup Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Signup Failed: {str(e)}")

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    try:
        user = db.query(models.User).filter(models.User.username == form_data.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"LOGIN ERROR DETAILS: {e}")
        raise e

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    existing_ailments: Optional[str] = None
    profile_picture: Optional[str] = None
    about_me: Optional[str] = None
    diet: Optional[str] = None
    activity_level: Optional[str] = None
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None
    allow_data_collection: Optional[bool] = None

@router.get("/profile", response_model=dict)
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "gender": current_user.gender,
        "dob": current_user.dob,
        "height": current_user.height,
        "weight": current_user.weight,
        "blood_type": current_user.blood_type,
        "existing_ailments": current_user.existing_ailments,
        "profile_picture": current_user.profile_picture,
        "about_me": current_user.about_me,
        "diet": current_user.diet,
        "activity_level": current_user.activity_level,
        "sleep_hours": current_user.sleep_hours,
        "stress_level": current_user.stress_level,
        "allow_data_collection": bool(current_user.allow_data_collection)
    }

@router.put("/profile")
def update_user_profile(profile: UserProfileUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if profile.email is not None: current_user.email = profile.email
    if profile.full_name is not None: current_user.full_name = profile.full_name
    if profile.gender is not None: current_user.gender = profile.gender
    if profile.dob is not None: current_user.dob = profile.dob
    if profile.height is not None: current_user.height = profile.height
    if profile.weight is not None: current_user.weight = profile.weight
    if profile.blood_type is not None: current_user.blood_type = profile.blood_type
    if profile.existing_ailments is not None: current_user.existing_ailments = profile.existing_ailments
    if profile.profile_picture is not None: current_user.profile_picture = profile.profile_picture
    if profile.about_me is not None: current_user.about_me = profile.about_me
    if profile.diet is not None: current_user.diet = profile.diet
    if profile.activity_level is not None: current_user.activity_level = profile.activity_level
    if profile.sleep_hours is not None: current_user.sleep_hours = profile.sleep_hours
    if profile.stress_level is not None: current_user.stress_level = profile.stress_level
    if profile.allow_data_collection is not None: 
        current_user.allow_data_collection = 1 if profile.allow_data_collection else 0
    
    db.commit()
    db.refresh(current_user)
    return {"status": "success", "message": "Profile updated", "user": {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "gender": current_user.gender,
        "dob": current_user.dob,
        "height": current_user.height,
        "weight": current_user.weight,
        "blood_type": current_user.blood_type,
        "existing_ailments": current_user.existing_ailments,
        "profile_picture": current_user.profile_picture,
        "about_me": current_user.about_me,
        "diet": current_user.diet,
        "activity_level": current_user.activity_level,
        "sleep_hours": current_user.sleep_hours,
        "stress_level": current_user.stress_level,
        "allow_data_collection": bool(current_user.allow_data_collection)
    }}
@router.get("/users", response_model=list[UserResponse])
def get_all_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    users = db.query(models.User).all()
    return users

# --- Admin Deep Dive Endpoints ---

class HealthRecordResponse(BaseModel):
    id: int
    record_type: str
    prediction: str
    timestamp: datetime
    data: str # JSON string
    class Config:
        from_attributes = True

class ChatLogResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    class Config:
        from_attributes = True

class UserFullResponse(UserResponse):
    health_records: list[HealthRecordResponse] = []
    chat_logs: list[ChatLogResponse] = []

@router.get("/users/{user_id}/full", response_model=UserFullResponse)
def get_user_full_details(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # --- AUDIT LOGGING ---
    try:
        audit_entry = models.AuditLog(
            admin_id=current_user.id,
            target_user_id=user_id,
            action="VIEW_SENSITIVE_DATA",
            details="Accessed full dossier"
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        print(f"Audit Log Error: {e}")

    # --- PRIVACY COMPLIANCE GATE ---
    # If user opted out (allow_data_collection=0), Redact Sensitive Data
    if not user.allow_data_collection:
        # We modify the response object, not the DB object
        # Pydantic will serialize this. We must ensure we return a structure masking the real relationships.
        # Since 'user' is an ORM object, accessing relationships loads them.
        # We should create the response manually or monkey-patch the list for this response context.
        user.health_records = [] 
        user.chat_logs = []
        user.about_me = "[REDACTED - PRIVACY RESTRICTED]"
        user.existing_ailments = "[REDACTED]"
        
    return user
