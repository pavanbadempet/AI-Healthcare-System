import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add root project directory to sys.path so 'backend' can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set TESTING flag to disable Global Exception Middleware (so we see tracebacks)
os.environ["TESTING"] = "true"
os.environ["GOOGLE_API_KEY"] = "dummy_key_for_testing"

# Import the APP and Database bases
from backend.main import app
from backend.database import Base, get_db
from backend.auth import get_current_user
from backend import models

# Use In-Memory SQLite for FAST isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Overriding the DB Dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def test_db():
    """
    Creates a fresh database for each test function.
    """
    # Ensure models are loaded so Base.metadata has tables
    from backend import models 
    print(f"[DEBUG] Creating tables: {list(Base.metadata.tables.keys())}")
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    # Use localhost to pass TrustedHostMiddleware check
    # raise_server_exceptions=True ensures 500 errors bubble up as Python exceptions
    with TestClient(app, base_url="http://localhost", raise_server_exceptions=True) as c:
        yield c

@pytest.fixture
def auth_header(client):
    """
    Registers a dummy user and returns a valid Authorization header.
    """
    user_data = {
        "username": "test_user_unique",
        "password": "StrongPassword123!",
        "email": "test@unique.com",
        "full_name": "Test User",
        "dob": "1990-01-01"
    }
    client.post("/signup", json=user_data)
    response = client.post("/token", data={"username": user_data["username"], "password": user_data["password"]})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
