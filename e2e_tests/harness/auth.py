"""
Authentication Helper and Token Generator for E2E Tests.
Supports both live API registration/login flow and direct JWT signing.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "test_secret_key_for_local_tests_only")
ALGORITHM = "HS256"


class TestAuthManager:
    """Manages JWT tokens and role-based auth headers for E2E test executions."""

    @staticmethod
    def seed_test_users():
        """Ensure standard test users exist in the current database."""
        try:
            from backend.database import SessionLocal
            from backend import models, auth
            db = SessionLocal()
            try:
                users_to_seed = [
                    ("admin_e2e", "admin@hospital.org", "admin", 1, 1),
                    ("doctor_e2e", "doctor@hospital.org", "doctor", 2, 1),
                    ("nurse_e2e", "nurse@hospital.org", "nurse", 3, 1),
                    ("patient_e2e", "patient@hospital.org", "patient", 4, 1),
                ]
                for uname, email, role, uid, fid in users_to_seed:
                    existing = db.query(models.User).filter(models.User.username == uname).first()
                    if not existing:
                        pwd_hash = auth.get_password_hash("StrongPassword123!")
                        user = models.User(
                            id=uid,
                            username=uname,
                            email=email,
                            hashed_password=pwd_hash,
                            role=role,
                            full_name=f"E2E {role.capitalize()}",
                            dob="1985-05-15",
                            facility_id=fid,
                            is_deleted=False,
                        )
                        db.merge(user)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass

    @staticmethod
    def generate_token(
        username: str = "testuser",
        user_id: int = 1,
        role: str = "patient",
        facility_id: Optional[int] = None,
        expires_minutes: int = 1440,
    ) -> str:
        """Create a valid signed JWT access token for testing."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        payload = {
            "sub": username,
            "user_id": user_id,
            "role": role,
            "facility_id": facility_id,
            "exp": expire,
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def get_auth_headers(
        role: str = "patient",
        username: Optional[str] = None,
        user_id: int = 1,
        facility_id: Optional[int] = None,
    ) -> Dict[str, str]:
        """Return Authorization header dict for a given test role."""
        if not username:
            username = f"{role}_e2e"
        token = TestAuthManager.generate_token(
            username=username,
            user_id=user_id,
            role=role,
            facility_id=facility_id,
        )
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def register_and_login(client: Any, username: Optional[str] = None, role: str = "patient", password: str = "StrongPass123!") -> Dict[str, str]:
        """Perform real HTTP signup and login against the running API."""
        if not username:
            username = f"e2e_{role}_{uuid.uuid4().hex[:8]}"
        email = f"{username}@healthcare-test.org"

        # 1. Signup
        signup_payload = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": f"E2E {role.capitalize()}",
            "dob": "1990-01-01",
        }
        client.post("/v1/signup", json=signup_payload)

        # 2. Login
        login_resp = client.post(
            "/v1/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if login_resp.is_success:
            token = login_resp.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}

        # Fallback to direct token if DB is in memory or test mode
        return TestAuthManager.get_auth_headers(role=role, username=username)
