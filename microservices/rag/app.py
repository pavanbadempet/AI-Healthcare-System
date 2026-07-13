import os
import sys
from typing import Any, Dict, Optional

# Ensure repository root is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Ensure the microservice itself runs locally
os.environ["MICROSERVICES_MODE"] = "false"

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from backend.licensing import verify_license_key


def enforce_license():
    license_key = os.environ.get("LICENSE_KEY", "").strip()
    if not license_key:
        raise HTTPException(status_code=403, detail="License key required for premium microservices.")
    is_valid, reason = verify_license_key(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=f"Invalid license key: {reason}")

# Import real package implementations
import clinical_rag_cache.prompt_registry as prompt_lib
import clinical_rag_cache.rag as rag_lib

app = FastAPI(title="Clinical RAG and Prompt Microservice", dependencies=[Depends(enforce_license)])

class CheckupInput(BaseModel):
    user_id: str
    record_id: str
    record_type: str
    data: dict
    prediction: str
    timestamp: str
    facility_id: Optional[str] = None

class InteractionInput(BaseModel):
    user_id: str
    interaction_id: str
    role: str
    content: str
    timestamp: str
    facility_id: Optional[str] = None

class SearchInput(BaseModel):
    user_id: str
    query: str
    n_results: int = 3
    facility_id: Optional[str] = None

@app.post("/rag/checkup")
def add_checkup(input_data: CheckupInput):
    success = rag_lib.add_checkup_to_db(
        user_id=input_data.user_id,
        record_id=input_data.record_id,
        record_type=input_data.record_type,
        data=input_data.data,
        prediction=input_data.prediction,
        timestamp=input_data.timestamp,
        facility_id=input_data.facility_id
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index checkup in RAG")
    return {"status": "success"}

@app.post("/rag/interaction")
def add_interaction(input_data: InteractionInput):
    success = rag_lib.add_interaction_to_db(
        user_id=input_data.user_id,
        interaction_id=input_data.interaction_id,
        role=input_data.role,
        content=input_data.content,
        timestamp=input_data.timestamp,
        facility_id=input_data.facility_id
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index interaction in RAG")
    return {"status": "success"}

@app.post("/rag/search")
def search_similar(input_data: SearchInput):
    results = rag_lib.search_similar_records(
        user_id=input_data.user_id,
        query=input_data.query,
        n_results=input_data.n_results,
        facility_id=input_data.facility_id
    )
    return {"results": results}

@app.delete("/rag/record/{record_id}")
def delete_record(record_id: str):
    success = rag_lib.delete_record_from_db(record_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete record from RAG")
    return {"status": "success"}

class AddInput(BaseModel):
    text: str
    metadata: Dict[str, Any]
    record_id: str

@app.post("/rag/add")
def add_document(input_data: AddInput):
    try:
        rag_lib.get_vector_store().add(
            input_data.text,
            input_data.metadata,
            input_data.record_id
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompt/get")
def get_prompt(name: str):
    try:
        prompt_text = prompt_lib.get_prompt(name)
        return {"prompt": prompt_text}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
