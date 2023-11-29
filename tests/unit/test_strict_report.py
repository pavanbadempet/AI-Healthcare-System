from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.report import router as report_router
import io

# Wrap router in App to avoid middleware scope issues
app = FastAPI()
app.include_router(report_router)

client = TestClient(app)

def test_analyze_report_valid_file():
    mock_result = {"summary": "Healthy"}
    
    with patch("backend.report.vision_service.analyze_lab_report", return_value=mock_result):
        # Create dummy file
        file_content = b"fake_image_content"
        
        resp = client.post(
            "/analyze/report",
            files={"file": ("test.jpg", file_content, "image/jpeg")}
        )
        
        assert resp.status_code == 200
        assert resp.json() == mock_result

def test_analyze_report_invalid_type():
    resp = client.post(
        "/analyze/report",
        files={"file": ("test.txt", b"text", "text/plain")}
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]

def test_analyze_report_exception():
    with patch("backend.report.vision_service.analyze_lab_report", side_effect=Exception("Vision API Down")):
        resp = client.post(
            "/analyze/report",
            files={"file": ("test.png", b"img", "image/png")}
        )
        assert resp.status_code == 500
        assert "Failed to analyze" in resp.json()["detail"]
