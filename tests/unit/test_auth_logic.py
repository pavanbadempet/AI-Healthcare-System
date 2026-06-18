from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from backend import auth


def test_password_hashing():
    pwd = "securepassword"
    hashed = auth.get_password_hash(pwd)
    assert hashed != pwd
    assert auth.verify_password(pwd, hashed) is True
    assert auth.verify_password("wrongpassword", hashed) is False

def test_access_token_creation():
    data = {"sub": "testuser"}
    token = auth.create_access_token(data)
    decoded = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

def test_access_token_expiry():
    data = {"sub": "testuser"}
    expires = timedelta(minutes=-1) # Already expired
    token = auth.create_access_token(data, expires_delta=expires)

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])

def test_secret_key_requires_environment_outside_testing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("TESTING", raising=False)

    with pytest.raises(RuntimeError):
        auth._load_secret_key()

def test_secret_key_allows_test_fallback_only_in_testing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("TESTING", "1")

    assert auth._load_secret_key() == "test_secret_key_for_local_tests_only"


def test_access_token_expire_minutes_from_env(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    assert auth._load_access_token_expire_minutes() == 45


def test_create_access_token_uses_configured_default_expiry(monkeypatch):
    monkeypatch.setattr(auth, "ACCESS_TOKEN_EXPIRE_MINUTES", 1)

    token = auth.create_access_token({"sub": "short_lived_user"})
    claims = jwt.get_unverified_claims(token)
    expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc)

    assert expires_at <= datetime.now(timezone.utc) + timedelta(minutes=2)
