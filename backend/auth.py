from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import re
import logging
from dotenv import load_dotenv

from . import models, database, schemas

# Initialize Logger
logger = logging.getLogger(__name__)

load_dotenv()

# --- Configuration & Constants ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("FATAL: SECRET_KEY environment variable is not set. Cannot start server.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

# --- Helper Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. Truncates to 72 bytes if necessary."""
    # Truncate BEFORE hashing - bcrypt has a 72-byte limit
    password_bytes = password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Claims to include in the token.
        expires_delta (timedelta, optional): Token expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    """
    Dependency to get the current authenticated user from JWT.
    """
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

def is_admin(user: models.User) -> bool:
    """Check if user has admin privileges."""
    # Check both username='admin' for backward compatibility and future role field
    return user.username == "admin" or getattr(user, 'is_admin', False)

# --- Endpoints ---

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)) -> models.User:
    """
    Register a new user.
    Enforces password complexity and checks for duplicate username/email.
    """
    try:
        # Password Complexity Check (Regex: 8+ chars, letters + numbers)
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$", user.password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters and contain both letters and numbers."
            )

        # Check Duplicate Username
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check Duplicate Email
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
        logger.error(f"Signup Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Signup Failed: {str(e)}")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)) -> Dict[str, str]:
    """
    Authenticate user and return JWT access token.
    """
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
        
        # --- AUDIT LOGGING ---
        try:
            audit_entry = models.AuditLog(
                admin_id=user.id, # Using admin_id field as 'actor_id'
                target_user_id=user.id,
                action="LOGIN_SUCCESS",
                details=f"User logged in from API. Timestamp: {datetime.now(timezone.utc)}"
            )
            db.add(audit_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Audit Log Failed: {e}")
            # Do not fail login if audit fails, just log error
            
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login Error: {e}")
        raise e

@router.get("/profile", response_model=Dict[str, Any])
def get_user_profile(current_user: models.User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return profile details for the currently logged-in user."""
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
def update_user_profile(
    profile: schemas.UserProfileUpdate, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """Update user profile fields."""
    
    # Update fields if provided
    for field, value in profile.model_dump(exclude_unset=True).items():
         if field == 'allow_data_collection':
             current_user.allow_data_collection = 1 if value else 0
         elif hasattr(current_user, field):
             setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": "success", 
        "message": "Profile updated", 
        "user": get_user_profile(current_user)
    }

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Admin only: Get all users."""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    users = db.query(models.User).all()
    return users

@router.get("/users/{user_id}/full", response_model=schemas.UserFullResponse)
def get_user_full_details(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Admin only: Get full user details including health records and chat logs (Audit Logged)."""
    if not is_admin(current_user):
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
        logger.error(f"Audit Log Error: {e}")

    # --- PRIVACY COMPLIANCE GATE ---
    if not user.allow_data_collection:
        # Redact Sensitive Data for privacy opted-out users
        user.health_records = [] 
        user.chat_logs = []
        user.about_me = "[REDACTED - PRIVACY RESTRICTED]"
        user.existing_ailments = "[REDACTED]"
        
    return user
