from unittest.mock import MagicMock, mock_open, patch

import numpy as np

# Import app to get router, but we might need to patch dependencies
# backend.main includes prediction router.
# Let's import prediction module directly to patch globals.
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.prediction
from backend.prediction import router

# Wrap router in App to avoid middleware scope issues
app = FastAPI()
app.include_router(router)
app.dependency_overrides[backend.prediction.auth.get_current_user] = lambda: backend.prediction.db_models.User(
    id=1,
    username="prediction_test_user",
    role="patient",
)

client = TestClient(app)


SENSITIVE_ERROR = "Model Failure with synthetic patient context"


def _assert_generic_prediction_failure(resp, caplog):
    body = resp.json()
    body_text = str(body)

    assert resp.status_code == 500
    assert "detail" in body
    assert SENSITIVE_ERROR not in body_text
    assert "synthetic patient context" not in body_text
    assert SENSITIVE_ERROR not in caplog.text
    assert "synthetic patient context" not in caplog.text


def test_load_pkl_hides_model_loader_error_details(caplog):
    sensitive_error = "pickle load failed db_password=secret-model patient_name=Sensitive User"
    caplog.set_level("ERROR", logger="backend.prediction")

    with patch("backend.prediction.os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=b"model-bytes")), \
         patch("backend.prediction.joblib.load", side_effect=Exception(sensitive_error)):
        result = backend.prediction.load_pkl(["diabetes_model.pkl"])

    assert result is None
    assert sensitive_error not in caplog.text
    assert "secret-model" not in caplog.text
    assert "Sensitive User" not in caplog.text


# --- Diabetes Tests ---

def test_predict_diabetes_success():
    # Setup Mock
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1]) # High Risk

    with patch("backend.prediction.diabetes_model", mock_model):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "High Risk"

def test_predict_diabetes_model_unavailable():
    # Force model to be None to hit 503
    with patch("backend.prediction.diabetes_model", None):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        assert resp.status_code == 503
        assert "not available" in resp.json()["detail"]

def test_predict_diabetes_exception(caplog):
    # Force exception during predict
    caplog.set_level("ERROR", logger="backend.prediction")
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception(SENSITIVE_ERROR)

    with patch("backend.prediction.diabetes_model", mock_model):
        resp = client.post("/predict/diabetes", json={
            "gender": 1, "age": 50, "hypertension": 0, "heart_disease": 0,
            "smoking_history": 1, "bmi": 25.0, "high_chol": 0, "physical_activity": 1, "general_health": 2
        })
        _assert_generic_prediction_failure(resp, caplog)

# --- Heart Tests ---

def test_predict_heart_success():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1]) # Disease

    with patch("backend.prediction.heart_model", mock_model):
        resp = client.post("/predict/heart", json={
            "age": 50, "sex": 1, "cp": 3, "trestbps": 145, "chol": 233,
            "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0,
            "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "Heart Disease Detected"

def test_predict_heart_model_unavailable():
    with patch("backend.prediction.heart_model", None):
        resp = client.post("/predict/heart", json={
            "age": 50, "sex": 1, "cp": 3, "trestbps": 145, "chol": 233,
            "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0,
            "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
        })
        assert resp.status_code == 503

def test_predict_heart_exception(caplog):
    caplog.set_level("ERROR", logger="backend.prediction")
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception(SENSITIVE_ERROR)

    with patch("backend.prediction.heart_model", mock_model):
        resp = client.post("/predict/heart", json={
            "age": 50, "sex": 1, "cp": 3, "trestbps": 145, "chol": 233,
            "fbs": 1, "restecg": 0, "thalach": 150, "exang": 0,
            "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
        })
        _assert_generic_prediction_failure(resp, caplog)

# --- Liver Tests ---

def test_predict_liver_success():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0]) # Healthy
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1,2,3,4,5,6]])

    with patch("backend.prediction.liver_model", mock_model), \
         patch("backend.prediction.liver_scaler", mock_scaler):

        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == "Healthy Liver"

def test_predict_liver_unavailable():
    # Test both model and scaler missing
    with patch("backend.prediction.liver_model", None):
        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        assert resp.status_code == 503

def test_predict_liver_exception(caplog):
    caplog.set_level("ERROR", logger="backend.prediction")
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception(SENSITIVE_ERROR)
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1,2,3,4,5,6]])

    with patch("backend.prediction.liver_model", mock_model), \
         patch("backend.prediction.liver_scaler", mock_scaler):

        resp = client.post("/predict/liver", json={
            "age": 45, "gender": 1, "total_bilirubin": 1.0,
            "alkaline_phosphotase": 100, "alamine_aminotransferase": 30,
            "albumin_and_globulin_ratio": 1.0, "direct_bilirubin": 0.5,
            "aspartate_aminotransferase": 30, "total_proteins": 6.0, "albumin": 3.0
        })
        _assert_generic_prediction_failure(resp, caplog)

def test_predict_kidney_exception(caplog):
    caplog.set_level("ERROR", logger="backend.prediction")
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception(SENSITIVE_ERROR)
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1, 2, 3]])

    with patch("backend.prediction.kidney_model", mock_model), \
         patch("backend.prediction.kidney_scaler", mock_scaler):
        resp = client.post("/predict/kidney", json={
            "age": 48.0, "bp": 80.0, "sg": 1.020, "al": 1.0, "su": 0.0,
            "rbc": 0, "pc": 0, "pcc": 0, "ba": 0,
            "bgr": 121.0, "bu": 36.0, "sc": 1.2, "sod": 135.0, "pot": 3.5,
            "hemo": 15.4, "pcv": 44.0, "wc": 7800.0, "rc": 5.2,
            "htn": 1, "dm": 1, "cad": 0, "appet": 0, "pe": 0, "ane": 0
        })
        _assert_generic_prediction_failure(resp, caplog)


def test_predict_lungs_exception(caplog):
    caplog.set_level("ERROR", logger="backend.prediction")
    mock_model = MagicMock()
    mock_model.predict.side_effect = Exception(SENSITIVE_ERROR)
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[1, 2, 3]])

    with patch("backend.prediction.lungs_model", mock_model), \
         patch("backend.prediction.lungs_scaler", mock_scaler):
        resp = client.post("/predict/lungs", json={
            "gender": 1, "age": 60, "smoking": 1, "yellow_fingers": 1,
            "anxiety": 1, "peer_pressure": 1, "chronic_disease": 1,
            "fatigue": 1, "allergy": 1, "wheezing": 1, "alcohol": 1,
            "coughing": 1, "shortness_of_breath": 1, "swallowing_difficulty": 1,
            "chest_pain": 1
        })
        _assert_generic_prediction_failure(resp, caplog)


def test_model_loading_failure(tmp_path):
    from backend.model_service import ModelService, ModelStatus

    service = ModelService(model_dir=str(tmp_path))
    with patch.dict(
        "os.environ",
        {"TESTING": "", "HF_TOKEN": "", "HF_DATASET_ID": ""},
    ):
        service.initialize()

    assert service._entries["diabetes"].status == ModelStatus.NOT_LOADED
    assert service._entries["heart"].status == ModelStatus.NOT_LOADED

