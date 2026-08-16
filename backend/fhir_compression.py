"""FHIR Compression Service.

Provides base85-encoded zlib compression for FHIR patient bundles,
optimizing payloads for low-bandwidth rural GSM and SMS transmission.
"""
import base64
import json
import logging
import zlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.rust_bridge import rust_bridge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fhir", tags=["FHIR Compression"])

class CompactRequest(BaseModel):
    fhir_bundle: dict

class DecompressRequest(BaseModel):
    compressed_data: str

@router.post("/compact")
def compact_fhir(body: CompactRequest):
    """Compress a FHIR JSON bundle into an ultra-dense base85 string via Rust/C-FFI engine."""
    try:
        base85_str, orig_sz, comp_sz, ratio = rust_bridge.compress_fhir_bundle_rust(body.fhir_bundle)
        return {
            "original_size": orig_sz,
            "compressed_size": comp_sz,
            "ratio": ratio,
            "payload": base85_str
        }
    except Exception:
        logger.error("FHIR bundle compression failed")
        raise HTTPException(status_code=400, detail="FHIR bundle compression failed.")

@router.post("/decompress")
def decompress_fhir(body: DecompressRequest):
    """Decompress a base85-encoded FHIR bundle back to its original JSON dict via Rust/C-FFI engine."""
    try:
        return rust_bridge.decompress_fhir_bundle_rust(body.compressed_data)
    except Exception:
        logger.error("FHIR bundle decompression failed")
        raise HTTPException(status_code=400, detail="FHIR bundle decompression failed.")
