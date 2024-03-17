"""
Backend Report Analysis Module
==============================
Handles the "Smart Lab Analyzer" feature.
Uses Computer Vision to extract numerical data 
from uploaded medical report images (PNG/JPG).

Author: Pavan Badempet
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import logging
from . import vision_service

# --- Logging ---
# logging.basicConfig(level=logging.INFO) # Handled in main.py
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze/report", response_model=Dict[str, Any])
async def analyze_report(file: UploadFile = File(...)) -> Dict[str, Any]:
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
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Report Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze report")
