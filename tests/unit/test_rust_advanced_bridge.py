"""
Unit tests for Advanced Rust Execution Engines:
- ECG Pan-Tompkins R-Peak Detection & HRV
- DICOM Pixel Matrix Normalization (HU + VOI LUT)
- FHIR Base85 Binary Compression & Decompression
- Multi-Omics VCF Parsing & Polygenic Risk Scoring
- Telemetry LTTB Downsampling
- Cryptographic Merkle Proof Attestation
"""

import hashlib
import math
from backend.rust_bridge import rust_bridge
from backend.ml.genomics_variant_pipeline import CLINICAL_VARIANT_CATALOG


def test_rust_ecg_pan_tompkins_and_hrv():
    sampling_rate = 250.0
    duration_s = 4.0
    total_samples = int(duration_s * sampling_rate)
    t = [i / sampling_rate for i in range(total_samples)]

    signal = [0.1 * math.sin(2 * math.pi * 1.0 * ti) for ti in t]
    spike_times = [0.8, 1.6, 2.4, 3.2]
    for st in spike_times:
        idx = int(st * sampling_rate)
        if 0 <= idx < len(signal):
            signal[idx] = 2.5
            if idx > 0: signal[idx-1] = 0.8
            if idx + 1 < len(signal): signal[idx+1] = 0.8

    r_peaks = rust_bridge.detect_ecg_r_peaks_rust(signal, sampling_rate)
    assert len(r_peaks) >= 3

    hr, sdnn, rmssd, pnn50 = rust_bridge.compute_hrv_metrics_rust(r_peaks, sampling_rate)
    assert 50.0 <= hr <= 100.0
    assert sdnn >= 0.0
    assert rmssd >= 0.0


def test_rust_dicom_pixel_normalization():
    raw_pixels = [0.0, 100.0, 500.0, 1000.0]
    normalized = rust_bridge.normalize_dicom_pixels_rust(
        raw_pixels, rescale_slope=1.0, rescale_intercept=-1000.0,
        window_center=40.0, window_width=400.0
    )
    assert len(normalized) == 4
    for val in normalized:
        assert 0.0 <= val <= 1.0


def test_rust_fhir_bundle_compression_and_decompression():
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": f"PATIENT-RUST-{i:03d}",
                    "gender": "female" if i % 2 == 0 else "male",
                    "birthDate": "1980-05-12",
                    "active": True,
                    "address": [{"city": "Hyderabad", "country": "India"}]
                }
            } for i in range(10)
        ]
    }

    b85_str, orig_sz, comp_sz, ratio = rust_bridge.compress_fhir_bundle_rust(fhir_bundle)
    assert isinstance(b85_str, str)
    assert len(b85_str) > 0
    assert comp_sz < orig_sz

    decompressed = rust_bridge.decompress_fhir_bundle_rust(b85_str)
    assert decompressed["resourceType"] == "Bundle"
    assert decompressed["entry"][0]["resource"]["id"] == "PATIENT-RUST-000"


def test_rust_vcf_parsing_and_prs():
    sample_vcf = """##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr10	114758349	rs7903146	C	T	99	PASS	GENE=TCF7L2
chr19	45411941	rs429358	T	C	99	PASS	GENE=APOE
chr22	50364718	rs6025	C	T	99	PASS	GENE=F5
"""
    variants, detected, prs = rust_bridge.parse_vcf_and_compute_prs_rust(sample_vcf, CLINICAL_VARIANT_CATALOG)
    assert len(variants) == 3
    assert len(detected) == 3
    assert "diabetes" in prs
    assert prs["diabetes"]["risk_multiplier"] > 1.0


def test_rust_lttb_downsampling():
    # 1,000 raw points downsampled to 50 points
    raw_points = [(float(i), math.sin(i * 0.05)) for i in range(1000)]
    downsampled = rust_bridge.downsample_lttb_rust(raw_points, threshold=50)
    assert len(downsampled) == 50
    assert downsampled[0] == raw_points[0]
    assert downsampled[-1] == raw_points[-1]


def test_rust_merkle_proof_verification():
    leaf_a = hashlib.sha256(b"LeafA").hexdigest()
    leaf_b = hashlib.sha256(b"LeafB").hexdigest()

    combined = (leaf_a + leaf_b).encode("utf-8") if leaf_a < leaf_b else (leaf_b + leaf_a).encode("utf-8")
    root_hash = hashlib.sha256(combined).hexdigest()

    is_valid = rust_bridge.verify_merkle_proof_rust(leaf_a, [leaf_b], root_hash)
    assert is_valid is True

    is_invalid = rust_bridge.verify_merkle_proof_rust(leaf_a, [leaf_b], "wrong_root_hash")
    assert is_invalid is False
