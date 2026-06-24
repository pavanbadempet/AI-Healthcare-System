import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import audit, database, models, schemas

# Initialize Logger
logger = logging.getLogger(__name__)

load_dotenv()

# --- Configuration & Constants ---
def _load_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        return secret_key
    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "test_secret_key_for_local_tests_only"
    raise RuntimeError("FATAL: SECRET_KEY environment variable is not set. Cannot start server.")


def _load_access_token_expire_minutes() -> int:
    raw_value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    try:
        minutes = int(raw_value)
    except ValueError:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer.")
    if minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")
    return minutes


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = _load_access_token_expire_minutes()
SIGNUP_FAILURE_DETAIL = "Signup failed. Please try again later."
LOGIN_FAILURE_DETAIL = "Login failed. Please try again later."
ADMIN_FACILITY_ACCESS_DETAIL = "Admin resource is outside the user's facility"

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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

    user = db.query(models.User).filter(models.User.username == username, models.User.is_deleted == False).first()
    if user is None:
        raise credentials_exception
    return user

def is_admin(user: models.User) -> bool:
    """Check if user has admin privileges."""
    # Strict Role-Based Access Control
    return getattr(user, 'role', 'patient') == 'admin'


def _scope_users_to_admin_facility(query, admin: models.User):
    query = query.filter(models.User.is_deleted == False)
    if admin.facility_id is None:
        return query
    return query.filter(models.User.facility_id == admin.facility_id)


def _ensure_admin_can_access_user(admin: models.User, user: models.User) -> None:
    if admin.facility_id is None:
        return
    if user.facility_id != admin.facility_id:
        raise HTTPException(status_code=403, detail=ADMIN_FACILITY_ACCESS_DETAIL)

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
    except Exception:
        db.rollback()
        logger.error("Signup failed")
        raise HTTPException(status_code=500, detail=SIGNUP_FAILURE_DETAIL)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)) -> Dict[str, str]:
    """
    Authenticate user and return JWT access token.
    """
    try:
        user = db.query(models.User).filter(models.User.username == form_data.username, models.User.is_deleted == False).first()
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        audit.record_audit_event(
            db,
            actor_user_id=user.id,
            target_user_id=user.id,
            action="LOGIN_SUCCESS",
            details={
                "resource_type": "auth_session",
                "outcome": "success",
                "occurred_at": datetime.now(timezone.utc),
            },
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Login failed")
        raise HTTPException(status_code=500, detail=LOGIN_FAILURE_DETAIL)

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
        "specialization": current_user.specialization,
        "allow_data_collection": bool(current_user.allow_data_collection),
        "role": getattr(current_user, "role", "patient")
    }

@router.put("/profile")
def update_user_profile(
    profile: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    """Update user profile fields."""

    updates = profile.model_dump(exclude_unset=True)
    for field, value in updates.items():
         if field == 'allow_data_collection':
             current_user.allow_data_collection = 1 if value else 0
         elif hasattr(current_user, field):
             setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    if updates:
        audit.record_audit_event(
            db,
            actor_user_id=current_user.id,
            target_user_id=current_user.id,
            action="UPDATE_PROFILE",
            details={
                "resource_type": "user_profile",
                "updated_fields": sorted(updates.keys()),
            },
        )

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
    users = _scope_users_to_admin_facility(db.query(models.User), current_user).all()
    return users

@router.get("/users/{user_id}/full", response_model=schemas.UserFullResponse)
def get_user_full_details(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Admin only: Get full user details including health records and chat logs (Audit Logged)."""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access only")

    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _ensure_admin_can_access_user(current_user, user)

    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=user_id,
        action="VIEW_SENSITIVE_DATA",
        details={"resource_type": "user_dossier", "resource_id": user_id},
    )

    # --- PRIVACY COMPLIANCE GATE ---
    # Eagerly load the collections so they can be read post-expunge
    _ = user.health_records
    _ = user.chat_logs

    # Detach from session so we don't accidentally commit redactions to OLTP DB
    db.expunge(user)

    if not user.allow_data_collection:
        # Redact Sensitive Data for privacy opted-out users
        user.health_records = []
        user.chat_logs = []
        user.about_me = "[REDACTED - PRIVACY RESTRICTED]"
        user.existing_ailments = "[REDACTED]"

    return user


def create_reset_token(email: str, username: str) -> str:
    """Create a 15-minute password reset JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": username,
        "email": email,
        "action": "reset_password",
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_reset_token(token: str, db: Session) -> Optional[models.User]:
    """Verify reset token and return matching User."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        action: str = payload.get("action")
        if username is None or action != "reset_password":
            return None
    except JWTError:
        return None
    return db.query(models.User).filter(models.User.username == username, models.User.is_deleted == False).first()


@router.post("/forgot-password")
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(database.get_db)
) -> dict[str, str]:
    """
    Generate a password reset link and deliver it through the email service.
    Always returns a generic success message to prevent user/email enumeration.
    """
    generic_success = {
        "status": "success",
        "message": "If this email is registered, a password reset link has been sent."
    }

    email = request.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email, models.User.is_deleted == False).first()
    if not user:
        return generic_success

    # Generate token
    token = create_reset_token(email=email, username=user.username)

    # Construct reset link
    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")
    reset_link = f"{frontend_url.rstrip('/')}/reset-password?token={token}"

    # Send email (which will simulate or send real SMTP)
    from .email_service import send_password_reset
    send_password_reset(to_email=user.email, username=user.username, reset_link=reset_link)

    return generic_success


@router.post("/reset-password")
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(database.get_db)
) -> dict[str, str]:
    """
    Reset user password using a valid reset token.
    """
    user = verify_reset_token(request.token, db)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    # Enforce password complexity
    if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$", request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters and contain both letters and numbers."
        )

    # Hash new password
    hashed_password = get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)

    # Audit event
    audit.record_audit_event(
        db,
        actor_user_id=user.id,
        target_user_id=user.id,
        action="PASSWORD_RESET_SUCCESS",
        details={
            "resource_type": "user_auth",
            "outcome": "success",
            "occurred_at": datetime.now(timezone.utc),
        },
    )

    return {"status": "success", "message": "Password has been reset successfully"}

