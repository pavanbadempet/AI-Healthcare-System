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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fhir", tags=["FHIR Compression"])

class CompactRequest(BaseModel):
    fhir_bundle: dict

class DecompressRequest(BaseModel):
    compressed_data: str

@router.post("/compact")
def compact_fhir(body: CompactRequest):
    """Compress a FHIR JSON bundle into an ultra-dense base85 string."""
    try:
        raw_json = json.dumps(body.fhir_bundle, separators=(",", ":"))
        json_bytes = raw_json.encode("utf-8")
        compressed = zlib.compress(json_bytes, level=9)
        base85_str = base64.b85encode(compressed).decode("ascii")

        ratio = len(base85_str) / len(raw_json) if raw_json else 1.0
        logger.info("Compressed FHIR bundle from %d to %d characters (Ratio: %.1f%%)",
                    len(raw_json), len(base85_str), ratio * 100)

        return {
            "original_size": len(raw_json),
            "compressed_size": len(base85_str),
            "ratio": round(ratio, 3),
            "payload": base85_str
        }
    except Exception as e:
        logger.error("FHIR bundle compression failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Compression failed: {str(e)}")

@router.post("/decompress")
def decompress_fhir(body: DecompressRequest):
    """Decompress a base85-encoded FHIR bundle back to its original JSON dict."""
    try:
        compressed_bytes = base64.b85decode(body.compressed_data.encode("ascii"))
        decompressed_bytes = zlib.decompress(compressed_bytes)
        fhir_dict = json.loads(decompressed_bytes.decode("utf-8"))
        return fhir_dict
    except Exception as e:
        logger.error("FHIR bundle decompression failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Decompression failed: {str(e)}")
