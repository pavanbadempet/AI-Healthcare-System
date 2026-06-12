

def _auth_headers(client, username: str = "prediction_api_user") -> dict[str, str]:
    password = "StrongPassword123!"
    signup = client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
            "full_name": "Synthetic Prediction User",
            "dob": "1990-01-01",
        },
    )
    assert signup.status_code == 200
    login = client.post("/token", data={"username": username, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Healthcare API"}

def test_heart_prediction_cdc(client):
    # Test with valid CDC BRFSS payload
    payload = {
        "age": 50,
        "sex": 1,
        "cp": 3,
        "trestbps": 145,
        "chol": 233,
        "fbs": 1,
        "restecg": 0,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 2.3,
        "slope": 0,
        "ca": 0,
        "thal": 1
    }
    response = client.post("/predict/heart", json=payload, headers=_auth_headers(client))
    assert response.status_code == 200
    json_data = response.json()
    assert "prediction" in json_data
    assert json_data["prediction"] in ["Heart Disease Detected", "Healthy Heart"]

def test_liver_prediction_extended(client):
    # Test with valid ILPD payload
    payload = {
        "age": 45,
        "gender": 1,
        "total_bilirubin": 0.7,
        "direct_bilirubin": 0.1,
        "alkaline_phosphotase": 187,
        "alamine_aminotransferase": 16,
        "aspartate_aminotransferase": 18,
        "total_proteins": 6.8,
        "albumin": 3.3,
        "albumin_and_globulin_ratio": 0.9
    }
    response = client.post("/predict/liver", json=payload, headers=_auth_headers(client))
    assert response.status_code == 200
    json_data = response.json()
    assert "prediction" in json_data

def test_diabetes_prediction(client):
    payload = {
        "gender": 1,
        "age": 45.0,
        "hypertension": 0,
        "heart_disease": 0,
        "smoking_history": 3, # Former
        "bmi": 27.5,
        "high_chol": 1,
        "physical_activity": 1,
        "general_health": 2
    }
    response = client.post("/predict/diabetes", json=payload, headers=_auth_headers(client))
    assert response.status_code == 200
    json_data = response.json()
    assert "prediction" in json_data

def test_kidney_prediction(client):
    # Test with valid UCI CKD payload (24 features)
    payload = {
        "age": 48.0, "bp": 80.0, "sg": 1.020, "al": 1.0, "su": 0.0,
        "rbc": 0, "pc": 0, "pcc": 0, "ba": 0, # Normal/NotPresent
        "bgr": 121.0, "bu": 36.0, "sc": 1.2, "sod": 135.0, "pot": 3.5,
        "hemo": 15.4, "pcv": 44.0, "wc": 7800.0, "rc": 5.2,
        "htn": 1, "dm": 1, "cad": 0, "appet": 0, "pe": 0, "ane": 0
    }
    response = client.post("/predict/kidney", json=payload, headers=_auth_headers(client))
    assert response.status_code == 200
    json_data = response.json()
    assert "prediction" in json_data
    # Check if raw value matches the string
    if json_data["raw"] == 1:
        assert "Detected" in json_data["prediction"]
    else:
        assert "Healthy" in json_data["prediction"]

def test_lung_prediction(client):
    payload = {
        "gender": 1, "age": 60, "smoking": 1, "yellow_fingers": 1,
        "anxiety": 1, "peer_pressure": 1, "chronic_disease": 1,
        "fatigue": 1, "allergy": 1, "wheezing": 1, "alcohol": 1,
        "coughing": 1, "shortness_of_breath": 1, "swallowing_difficulty": 1,
        "chest_pain": 1
    }
    response = client.post("/predict/lungs", json=payload, headers=_auth_headers(client))
    assert response.status_code == 200
    assert "prediction" in response.json()

def test_chat_context(client):
    """Chat endpoint returns a response when called with authenticated user and prediction context."""
    from unittest.mock import patch

    from langchain_core.messages import AIMessage

    headers = _auth_headers(client, username="chat_context_user")

    payload = {
        "message": "What does my heart result mean?",
        "history": [],
        "current_context": {
            "Heart Disease": {"prediction": "Healthy Heart", "data": {"age": 25}},
            "Diabetes": {"prediction": "High Risk", "data": {"glucose": 150}},
        },
    }

    mock_result = {"messages": [AIMessage(content="Your heart result looks normal. Please consult a doctor.")]}
    with patch("backend.agent.medical_agent.invoke", return_value=mock_result):
        response = client.post("/chat", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
