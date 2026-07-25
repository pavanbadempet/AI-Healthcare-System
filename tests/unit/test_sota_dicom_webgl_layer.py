"""
Unit tests for SOTA DICOM WebGL Engine (backend/sota_dicom_webgl_layer.py).
"""

from backend.sota_dicom_webgl_layer import SOTADicomWebGLLayerEngine


def test_dicom_slice_decompression():
    engine = SOTADicomWebGLLayerEngine()

    raw_slice_bytes = b"DICOM_HEADER_DUMMY_PIXEL_DATA"
    result = engine.decompress_dicom_slice(raw_slice_bytes, slice_id="CT_CHEST_001")

    assert result.slice_id == "CT_CHEST_001"
    assert result.dimensions == [512, 512]
    assert result.hounsfield_min == -1000.0
    assert result.is_simd_decompressed
    assert result.decompression_time_ms >= 0.0
