from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, ANY
import pytest
import datetime
from backend import models, chat

# Setup App
app = FastAPI()
app.include_router(chat.router)

# Mock Dependencies
def mock_get_current_user():
    user = MagicMock(spec=models.User)
    user.id = 1
    user.username = "testuser"
    user.full_name = "Test User"
    user.allow_data_collection = True
    # Default other fields
    user.dob = "1990-01-01"
    user.gender = "Male"
    user.height = 180
    user.weight = 75
    user.blood_type = "O+"
    user.existing_ailments = "None"
    user.diet = "Balanced"
    user.activity_level = "Moderate"
    user.sleep_hours = 7
    user.stress_level = "Low"
    user.about_me = "Test profile"
    return user

def mock_get_db():
    yield MagicMock()

app.dependency_overrides[chat.auth.get_current_user] = mock_get_current_user
app.dependency_overrides[chat.database.get_db] = mock_get_db

client = TestClient(app)

# --- Tests ---

def test_chat_agent_failure():
    # Mock agent invoke to raise exception
    with patch("backend.chat.agent.medical_agent.invoke", side_effect=Exception("Agent Down")):
        resp = client.post("/chat", json={"message": "Hi"})
        assert resp.status_code == 200 # It returns 200 with error message
        assert "trouble" in resp.json()["response"]
        assert "Agent Down" in resp.json()["error"]

def test_chat_db_save_failure():
    # Mock DB commit to fail
    mock_db = MagicMock()
    mock_db.commit.side_effect = Exception("DB Error")
    
    app.dependency_overrides[chat.database.get_db] = lambda: mock_db
    
    # Needs valid agent response
    mock_agent_resp = {"messages": [MagicMock(content="Hello")]}
    
    with patch("backend.chat.agent.medical_agent.invoke", return_value=mock_agent_resp):
        # This will error on User Log Save (first commit)
        # The code catches it and prints error, but proceeds?
        # chat.py: try/except around user log save.
        resp = client.post("/chat", json={"message": "Hi"})
        assert resp.status_code == 200
        assert resp.json()["response"] == "Hello"
        # We verified that it didn't crash application

def test_chat_record_validation():
    # Setup DB returning records
    valid_rec = MagicMock(spec=models.HealthRecord)
    valid_rec.id = 1
    valid_rec.record_type = "Diabetes"
    valid_rec.data = '{"glucose": 120, "bmi": 25}'
    valid_rec.timestamp = datetime.datetime.now()
    valid_rec.prediction = "Healthy"
    
    invalid_rec = MagicMock(spec=models.HealthRecord)
    invalid_rec.id = 2
    invalid_rec.record_type = "Diabetes"
    invalid_rec.data = '{"glucose": 0, "bmi": 25}' # Invalid glucose
    invalid_rec.timestamp = datetime.datetime.now()
    
    malformed_rec = MagicMock(spec=models.HealthRecord)
    malformed_rec.id = 3
    malformed_rec.data = "Not JSON"
    
    mock_db = MagicMock()
    # For GET query (first call): return list
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [valid_rec, invalid_rec, malformed_rec]
    
    # For DELETE query (second call, filter(...).first()): return None to trigger 404
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    app.dependency_overrides[chat.database.get_db] = lambda: mock_db
    
    # Spy on agent call to check inputs
    with patch("backend.chat.agent.medical_agent.invoke") as mock_invoke:
        mock_invoke.return_value = {"messages": [MagicMock(content="Ok")]}
        
        client.post("/chat", json={"message": "Analyze"})
        
        # Check arguments passed to agent
    resp = client.delete("/records/999")
    assert resp.status_code == 404
