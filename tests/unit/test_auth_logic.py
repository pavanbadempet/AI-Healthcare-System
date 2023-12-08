import pytest
from backend import auth
from jose import jwt
from datetime import timedelta

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
