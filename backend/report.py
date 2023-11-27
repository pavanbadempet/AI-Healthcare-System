
from fastapi import APIRouter, UploadFile, File, HTTPException
from . import vision_service
import shutil

router = APIRouter()

@router.post("/analyze/report")
async def analyze_report(file: UploadFile = File(...)):
    """
    Accepts an image file, analyzes it using GenAI, and returns structured medical data.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPEG or PNG image.")
    
    try:
        # Read file
        contents = await file.read()
        
        # Analyze
        result = vision_service.analyze_lab_report(contents)
        
        return result
        
    except Exception as e:
        print(f"Report Analysis Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze report")
