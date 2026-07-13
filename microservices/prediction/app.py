import os
import sys

# Ensure repository root is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Ensure the microservice itself runs prediction locally
os.environ["MICROSERVICES_MODE"] = "false"

import uvicorn
from fastapi import Depends, FastAPI, HTTPException

from backend.licensing import verify_license_key
from backend.model_service import model_service
from backend.prediction import initialize_models
from backend.schemas import DiabetesInput, HeartInput, KidneyInput, LiverInput, LungInput


def enforce_license():
    license_key = os.environ.get("LICENSE_KEY", "").strip()
    if not license_key:
        raise HTTPException(status_code=403, detail="License key required for premium microservices.")
    is_valid, reason = verify_license_key(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=f"Invalid license key: {reason}")

app = FastAPI(title="AI Healthcare Prediction Microservice", dependencies=[Depends(enforce_license)])

@app.on_event("startup")
def startup():
    initialize_models()

@app.post("/predict/diabetes")
def predict_diabetes(data: DiabetesInput):
    res = model_service.predict_diabetes(data)
    return {
        "prediction": res.prediction,
        "raw": int(res.raw),
        "confidence": float(res.confidence),
        "risk_level": res.risk_level,
        "disclaimer": res.disclaimer
    }

@app.post("/predict/heart")
def predict_heart(data: HeartInput):
    res = model_service.predict_heart(data)
    return {
        "prediction": res.prediction,
        "raw": int(res.raw),
        "confidence": float(res.confidence),
        "risk_level": res.risk_level,
        "disclaimer": res.disclaimer
    }

@app.post("/predict/liver")
def predict_liver(data: LiverInput):
    res = model_service.predict_liver(data)
    return {
        "prediction": res.prediction,
        "raw": int(res.raw),
        "confidence": float(res.confidence),
        "risk_level": res.risk_level,
        "disclaimer": res.disclaimer
    }

@app.post("/predict/kidney")
def predict_kidney(data: KidneyInput):
    res = model_service.predict_kidney(data)
    return {
        "prediction": res.prediction,
        "raw": int(res.raw),
        "confidence": float(res.confidence),
        "risk_level": res.risk_level,
        "disclaimer": res.disclaimer
    }

@app.post("/predict/lungs")
def predict_lungs(data: LungInput):
    res = model_service.predict_lungs(data)
    return {
        "prediction": res.prediction,
        "raw": int(res.raw),
        "confidence": float(res.confidence),
        "risk_level": res.risk_level,
        "disclaimer": res.disclaimer
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
