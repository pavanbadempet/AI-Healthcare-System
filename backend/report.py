"""
Backend Report Analysis Module
==============================
Handles the "Smart Lab Analyzer" feature.
Uses Computer Vision to extract numerical data
from uploaded medical report images (PNG/JPG).

Author: Pavan Badempet
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from . import auth, database, models, pdf_service, vision_service

# --- Logging ---
# logging.basicConfig(level=logging.INFO) # Handled in main.py
logger = logging.getLogger(__name__)

router = APIRouter()
REPORT_ANALYSIS_FAILURE_DETAIL = "Failed to analyze report"
HEALTH_REPORT_FAILURE_DETAIL = "Failed to generate health report"
REPORT_ANALYSIS_DISCLAIMER = (
    "This AI-assisted report analysis is for informational support only and is not a medical diagnosis. "
    "Please consult a qualified clinician for diagnosis, treatment, or emergencies."
)


def _with_report_analysis_disclaimer(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(result)
    payload.setdefault("disclaimer", REPORT_ANALYSIS_DISCLAIMER)
    return payload

@router.post("/analyze/report", response_model=Dict[str, Any])
async def analyze_report(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
) -> Dict[str, Any]:
    """
    Analyze an uploaded medical report image.

    Args:
        file (UploadFile): Image file (JPEG/PNG).

    Returns:
        dict: Extracted metrics and summary.

    Raises:
        HTTPException(400): Invalid file type.
        HTTPException(500): Analysis failure.
    """
    # 1. Validate File Type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a JPEG or PNG image."
        )

    try:
        # 2. Read File
        contents = await file.read()

        # 3. Analyze via Vision Service
        result = vision_service.analyze_lab_report(contents)

        return _with_report_analysis_disclaimer(result)

    except HTTPException as he:
        raise he
    except Exception:
        logger.error("Report analysis failed")
        raise HTTPException(status_code=500, detail=REPORT_ANALYSIS_FAILURE_DETAIL)

# --- PDF Download Endpoint ---
from fastapi.responses import Response
from sqlalchemy.orm import Session


@router.get("/reports/download/health-report")
def download_health_report(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Generate and download a comprehensive health report PDF for the authenticated user.
    """
    try:
        # 1. Fetch latest health record (Simulating a general summary for now)
        # In a real app, we'd aggregate multiple records.
        # For now, let's grab the most recent prediction if any.
        latest_record = db.query(models.HealthRecord).filter(
            models.HealthRecord.user_id == current_user.id
        ).order_by(models.HealthRecord.timestamp.desc()).first()

        report_data = {
            "age": 30, # Default/Placeholder if profile empty
            "gender": "Unknown"
        }

        # Merge Profile Data
        if current_user.about_me:
            # Simplistic parsing or just dumping raw profile fields
            report_data["about"] = current_user.about_me

        prediction_val = "General Health Summary"
        advice_list = ["maintain a balanced diet", "regular exercise"]

        if latest_record:
            prediction_val = f"{latest_record.record_type.capitalize()} Analysis: {latest_record.prediction}"
            # Extract clinical data
            import json
            try:
                if latest_record.data:
                    parsed_data = json.loads(latest_record.data)
                    report_data.update(parsed_data)
            except Exception:
                logger.warning("Failed to parse health record data")

        # 2. Generate PDF using the existing service
        pdf_bytes = pdf_service.generate_medical_report(
            user_name=current_user.username,
            report_type="Comprehensive Health Profile",
            prediction=prediction_val,
            data=report_data,
            advice=advice_list
        )

        # 3. Return as downloadable file
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Health_Report.pdf"}
        )

    except Exception:
        logger.error("PDF generation failed")
        # Return a fallback PDF or 500 based on preference.
        # For now, let's try to return a simple error PDF if possible, or just raise 500
        raise HTTPException(status_code=500, detail=HEALTH_REPORT_FAILURE_DETAIL)
