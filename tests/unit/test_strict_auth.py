from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import timedelta
import pytest
from jose import JWTError 

# Import module to patch globals or functions
import backend.auth
from backend.auth import router, get_current_user, create_access_token
from backend import models

# Setup App
app = FastAPI()
app.include_router(router)

# Dummy dependency override for DB
def mock_get_db():
    try:
        yield MagicMock()
    finally:
        pass

app.dependency_overrides[backend.auth.database.get_db] = mock_get_db
client = TestClient(app)

# --- Token Logic Tests ---

def test_create_access_token_expiry():
    # Test custom expiry
    delta = timedelta(minutes=100)
    token = create_access_token({"sub": "test"}, expires_delta=delta)
    # Decode and check exp
    decoded = backend.auth.jwt.decode(token, backend.auth.SECRET_KEY, algorithms=[backend.auth.ALGORITHM])
    # Roughly check if exp is > now + 90 mins
    import time
    assert decoded["exp"] > time.time() + (90 * 60)

# --- get_current_user Tests ---
# get_current_user is used as a dependency. We can call it directly or via a dummy route.
@app.get("/test/me")
def protected_route(user=Depends(get_current_user)):
    return {"username": user.username}

def test_get_current_user_jwt_error():
    # Mock jwt.decode to raise JWTError
    with patch("backend.auth.jwt.decode", side_effect=JWTError()):
        resp = client.get("/test/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401
        assert "Could not validate credentials" in resp.json()["detail"]

def test_get_current_user_no_sub():
    # Mock jwt.decode to return payload without 'sub'
    with patch("backend.auth.jwt.decode", return_value={"other": "data"}):
        resp = client.get("/test/me", headers={"Authorization": "Bearer valid_token"})
        assert resp.status_code == 401

def test_get_current_user_not_found():
    # Mock jwt.decode success
    with patch("backend.auth.jwt.decode", return_value={"sub": "ghost_user"}):
        # Mock DB query to return None
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # We need to inject this mock_db into the dependency
        app.dependency_overrides[backend.auth.database.get_db] = lambda: mock_db
        
        resp = client.get("/test/me", headers={"Authorization": "Bearer valid_token"})
        assert resp.status_code == 401

# --- Signup Error Tests ---

def test_signup_db_integrity_error():
    # Mock DB commit to raise IntegrityError (e.g. race condition)
    # Note: The code in auth.py doesn't show explicit try/except around db.add/commit for generic errors
    # apart from the username check.
    # If standard SQLAlchemy error occurs, FastAPI returns 500.
    # We want to verify that behavior or if there's custom handling I missed.
    # Looking at auth.py specific to Lines 95-100... it explicitly checks username existence.
    pass 
    # If I want to test lines 10 or generic DB failures:
    mock_db = MagicMock()
    # Ensure username check passes (returns None)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    # Fail on add or commit
    mock_db.commit.side_effect = Exception("DB Down")
    
    app.dependency_overrides[backend.auth.database.get_db] = lambda: mock_db
    
    resp = client.post("/signup", json={
        "username": "crash",
        "password": "Password123!",
        "email": "crash@test.com",
        "full_name": "Crash",
        "dob": "1990-01-01"
    })
    # Expect 500
    assert resp.status_code == 500
