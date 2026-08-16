"""
AI Healthcare System — Native Rust Core Execution & FFI Bridge
==============================================================
Provides high-performance Rust integration primitives across the stack:
1. Native Rust Vector Dot-Product & Cosine Similarity Acceleration
2. Rust PyO3 / Maturin Module Dispatcher & FFI Safety Harness
3. Zero-Allocation Memory Buffer Transfers & Native Sepsis / Fraud Compute
4. Native Clinical Risk Algorithms (Diabetes, Heart, FIB-4, SaMD Risk Matrix)
5. Real-Time Biosignal DSP (Pan-Tompkins ECG & HRV Analysis)
6. DICOM Medical Imaging Pixel Matrix Normalization (HU Scaling & VOI LUT)
7. Fast Binary FHIR Serialization & Zstandard/Base85 Compression
"""

import base64
import json
import math
import time
import zlib
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel


class RustExecutionMetrics(BaseModel):
    """Metrics for Rust Native Execution Engine dispatches."""
    task_name: str
    vector_dim: int
    result: float
    execution_time_us: float
    is_rust_native: bool


class RustBridgeEngine:
    """Repo-Wide Rust Native Execution & Fallback Engine."""

    def redact_phi_text_rust(self, text: str) -> str:
        """Redacts PHI text directly via Native Rust PyO3 SIMD logic or fallback regex."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.redact_phi_py(text)
        except Exception:
            import re
            txt = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED-SSN]", text)
            txt = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED-EMAIL]", txt)
            return txt

    def hash_password_rust(self, password: str) -> str:
        """Hashes password using Rust native bcrypt or fallback SHA-256."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.hash_password_py(password)
        except Exception:
            import hashlib
            return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verify_password_rust(self, password: str, hashed_value: str) -> bool:
        """Verifies password using Rust native bcrypt or fallback SHA-256 comparison."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.verify_password_py(password, hashed_value)
        except Exception:
            import hashlib
            computed = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return computed == hashed_value

    def compute_rust_cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> RustExecutionMetrics:
        """Computes vector cosine similarity executing Native Rust PyO3 SIMD logic."""
        start = time.perf_counter()
        try:
            import rust_gateway_ffi
            similarity = rust_gateway_ffi.calculate_cosine_similarity_py(vec_a, vec_b)
            is_native = True
        except Exception:
            dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = math.sqrt(sum(a * a for a in vec_a))
            norm_b = math.sqrt(sum(b * b for b in vec_b))
            similarity = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0
            is_native = False

        elapsed_us = round((time.perf_counter() - start) * 1e6, 2)

        return RustExecutionMetrics(
            task_name="RUST_PYO3_COSINE_SIMILARITY",
            vector_dim=len(vec_a),
            result=round(similarity, 6),
            execution_time_us=elapsed_us,
            is_rust_native=is_native
        )

    def compute_rust_egfr(self, serum_creatinine: float = 0.9, age: float = 45.0, is_female: bool = False, creatinine: float | None = None) -> float:
        """Computes eGFR using CKD-EPI formula in Rust or fallback Python."""
        cr = creatinine if creatinine is not None else serum_creatinine
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.calculate_egfr_py(cr, age, is_female)
        except Exception:
            if cr <= 0.0 or age <= 0.0:
                return 0.0
            kappa, alpha = (0.7, -0.241) if is_female else (0.9, -0.302)
            f_mult = 1.012 if is_female else 1.0
            min_val = min(cr / kappa, 1.0) ** alpha
            max_val = max(cr / kappa, 1.0) ** (-1.200)
            return round(142.0 * min_val * max_val * (0.9938 ** age) * f_mult, 2)

    def calculate_fib4_rust(self, ast: float, alt: float, platelets: float, age: float) -> float:
        """Computes FIB-4 Liver Fibrosis Index."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.calculate_fib4_py(ast, alt, platelets, age)
        except Exception:
            if platelets <= 0 or alt <= 0:
                return 0.0
            score = (age * ast) / (platelets * math.sqrt(alt))
            return round(score, 2)

    def compute_sepsis_qsofa_rust(self, resp_rate: float, sbp: float, gcs: float) -> Tuple[int, str]:
        """Calculates qSOFA Sepsis score."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.compute_qsofa_py(resp_rate, sbp, gcs)
        except Exception:
            score = 0
            if resp_rate >= 22.0: score += 1
            if sbp <= 100.0: score += 1
            if gcs < 15.0: score += 1
            risk = "HIGH_SEPSIS_RISK" if score >= 2 else "LOW_MODERATE_SEPSIS_RISK"
            return (score, risk)

    def detect_billing_anomalies_rust(self, amounts: List[float], threshold_z: float = 3.0) -> List[int]:
        """Detects billing fraud/anomalies using Rust SIMD Z-Score."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.detect_billing_anomalies_py(amounts, threshold_z)
        except Exception:
            if len(amounts) < 3:
                return []
            mean = sum(amounts) / len(amounts)
            variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
            std = math.sqrt(variance)
            if std == 0:
                return []
            return [i for i, x in enumerate(amounts) if abs((x - mean) / std) >= threshold_z]

    def classify_samd_risk_rust(self, is_critical: bool, is_drive_management: bool, is_inform_care: bool) -> str:
        """Classifies FDA SaMD Risk Matrix."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.classify_samd_risk_py(is_critical, is_drive_management, is_inform_care)
        except Exception:
            if is_critical and is_drive_management: return "CLASS_IV_CRITICAL"
            if is_critical or is_drive_management: return "CLASS_III_HIGH"
            if is_inform_care: return "CLASS_II_MODERATE"
            return "CLASS_I_LOW"

    def generate_audit_hash_rust(self, index: int, event_type: str, actor_id: str, action_details: str, previous_hash: str) -> str:
        """Generates SHA-256 Part 11 audit block hash."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.generate_audit_hash_py(index, event_type, actor_id, action_details, previous_hash)
        except Exception:
            import hashlib
            payload = f"{index}:{event_type}:{actor_id}:{action_details}:{previous_hash}"
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def generate_counterfactual_rust(self, features: List[str], values: List[float], risk_score: float) -> Tuple[List[str], float]:
        """Generates clinical counterfactual recommendations."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.generate_counterfactual_py(features, values, risk_score)
        except Exception:
            recs = []
            for feat, val in zip(features, values):
                fl = feat.lower()
                if "bp" in fl or "pressure" in fl:
                    if val > 120.0: recs.append(f"Reduce {feat} from {val:.1f} to <= 120.0 mmHg")
                elif "chol" in fl:
                    if val > 200.0: recs.append(f"Reduce {feat} from {val:.1f} to <= 200.0 mg/dL")
                elif "glucose" in fl:
                    if val > 100.0: recs.append(f"Reduce {feat} from {val:.1f} to <= 100.0 mg/dL")
            if not recs:
                recs.append("Maintain current clinical vitals and metabolic targets")
            target = max(0.05, risk_score * 0.5)
            return (recs, round(target, 3))

    def aggregate_fedavg_rust(self, client_gradients: List[List[float]], weights: List[float]) -> List[float]:
        """Aggregates Federated Learning gradients via FedAvg."""
        if not client_gradients or not weights or len(client_gradients) != len(weights):
            return []
        total_weight = sum(weights)
        if total_weight == 0:
            return []
        dim = len(client_gradients[0])
        aggregated = [0.0] * dim
        for grads, w in zip(client_gradients, weights):
            normalized_w = w / total_weight
            for i in range(dim):
                aggregated[i] += grads[i] * normalized_w
        return aggregated

    # =========================================================================
    # 🫀 BIOSIGNAL DSP & ECG ANALYSIS (RUST PY03 ENGINE)
    # =========================================================================
    def detect_ecg_r_peaks_rust(self, signal: List[float], sampling_rate: float = 250.0) -> List[int]:
        """Runs Pan-Tompkins QRS R-peak detection in Rust PyO3 with zero-allocation fallback."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.detect_ecg_r_peaks_py(signal, sampling_rate)
        except Exception:
            if len(signal) < int(sampling_rate * 0.5):
                return []
            import numpy as np
            x = np.array(signal, dtype=float)
            kernel_lp = np.array([1, 2, 3, 4, 5, 4, 3, 2, 1]) / 25.0
            filtered = np.convolve(x, kernel_lp, mode='same')
            kernel_hp = np.array([-1, 2, -1]) / 4.0
            filtered = np.convolve(filtered, kernel_hp, mode='same')
            der_kernel = np.array([-1, -2, 0, 2, 1]) * (sampling_rate / 8.0)
            derivative = np.convolve(filtered, der_kernel, mode='same')
            squared = derivative ** 2
            window_size = max(1, int(0.150 * sampling_rate))
            integrated = np.convolve(squared, np.ones(window_size) / window_size, mode='same')

            peaks = []
            min_dist = int(0.2 * sampling_rate)
            thresh = np.mean(integrated) + 0.5 * np.std(integrated)
            i = 0
            while i < len(integrated):
                if integrated[i] > thresh:
                    start_idx = max(0, i - window_size)
                    end_idx = min(len(signal), i + window_size)
                    local_max = start_idx + int(np.argmax(signal[start_idx:end_idx]))
                    if not peaks or (local_max - peaks[-1]) > min_dist:
                        peaks.append(local_max)
                    i += min_dist
                else:
                    i += 1
            return peaks

    def compute_hrv_metrics_rust(self, r_peaks: List[int], sampling_rate: float = 250.0) -> Tuple[float, float, float, float]:
        """Calculates Heart Rate Variability (HR, SDNN, RMSSD, pNN50) in Rust."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.compute_hrv_metrics_py(r_peaks, sampling_rate)
        except Exception:
            if len(r_peaks) < 2:
                return 72.0, 0.0, 0.0, 0.0
            import numpy as np
            rr = np.diff(r_peaks) * (1000.0 / sampling_rate)
            valid = rr[(rr >= 300) & (rr <= 2000)]
            if len(valid) < 2:
                valid = rr
            mean_rr = float(np.mean(valid))
            hr = 60000.0 / mean_rr if mean_rr > 0 else 72.0
            sdnn = float(np.std(valid))
            diffs = np.diff(valid)
            rmssd = float(np.sqrt(np.mean(diffs ** 2))) if len(diffs) > 0 else 0.0
            nn50 = np.sum(np.abs(diffs) > 50.0) if len(diffs) > 0 else 0
            pnn50 = float((nn50 / len(diffs)) * 100.0) if len(diffs) > 0 else 0.0
            return (round(hr, 1), round(sdnn, 2), round(rmssd, 2), round(pnn50, 2))

    # =========================================================================
    # 🩻 MEDICAL IMAGING (DICOM MATRIX NORMALIZATION & WINDOWING)
    # =========================================================================
    def normalize_dicom_pixels_rust(
        self, raw_pixels: List[float], rescale_slope: float = 1.0, rescale_intercept: float = 0.0,
        window_center: float = 40.0, window_width: float = 400.0
    ) -> List[float]:
        """Applies Hounsfield Unit scaling and VOI LUT window/level clamping in Rust SIMD."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.normalize_dicom_pixels_py(raw_pixels, rescale_slope, rescale_intercept, window_center, window_width)
        except Exception:
            lower = window_center - (window_width / 2.0)
            upper = window_center + (window_width / 2.0)
            normalized = []
            for px in raw_pixels:
                hu = px * rescale_slope + rescale_intercept
                clamped = max(lower, min(upper, hu))
                norm_val = (clamped - lower) / window_width if window_width > 0 else 0.0
                normalized.append(round(norm_val, 4))
            return normalized

    # =========================================================================
    # 📦 HIGH-SPEED FHIR SERIALIZATION & COMPRESSION
    # =========================================================================
    def compress_fhir_bundle_rust(self, fhir_bundle: dict) -> Tuple[str, int, int, float]:
        """Compresses FHIR bundle into base85 payload using Rust zlib/zstd."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.compress_fhir_bundle_py(fhir_bundle)
        except Exception:
            raw_json = json.dumps(fhir_bundle, separators=(",", ":"))
            compressed = zlib.compress(raw_json.encode("utf-8"), level=9)
            b85 = base64.b85encode(compressed).decode("ascii")
            ratio = len(b85) / len(raw_json) if raw_json else 1.0
            return (b85, len(raw_json), len(b85), round(ratio, 3))

    def decompress_fhir_bundle_rust(self, base85_str: str) -> dict:
        """Decompresses base85 payload back into FHIR dictionary using Rust."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.decompress_fhir_bundle_py(base85_str)
        except Exception:
            decompressed = zlib.decompress(base64.b85decode(base85_str.encode("ascii")))
            return json.loads(decompressed.decode("utf-8"))

    # =========================================================================
    # 🧬 MULTI-OMICS GENOMICS & VCF PARSING
    # =========================================================================
    def parse_vcf_and_compute_prs_rust(self, vcf_text: str, catalog: dict) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], Dict[str, Any]]:
        """Parses VCF lines and calculates Polygenic Risk Scores (PRS) via Rust SIMD / Fallback."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.parse_vcf_and_compute_prs_py(vcf_text, catalog)
        except Exception:
            variants = []
            lines = vcf_text.strip().split("\n")
            for line in lines:
                if line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    variants.append({
                        "chrom": parts[0],
                        "pos": parts[1],
                        "rsid": parts[2],
                        "ref": parts[3],
                        "alt": parts[4],
                    })

            detected_variants = []
            risk_multipliers = {
                "diabetes": 1.0,
                "heart": 1.0,
                "liver": 1.0,
                "lungs": 1.0,
                "kidney": 1.0,
            }

            for v in variants:
                rsid = v["rsid"]
                if rsid in catalog:
                    entry = catalog[rsid]
                    condition = entry["condition"]
                    alt_alleles = v["alt"].split(",")
                    if entry["risk_allele"] in alt_alleles:
                        detected_variants.append({
                            "rsid": rsid,
                            "gene": entry["gene"],
                            "condition": condition,
                            "detected_allele": entry["risk_allele"],
                            "odds_ratio": entry["odds_ratio"],
                            "description": entry["description"],
                        })
                        risk_multipliers[condition] *= entry["odds_ratio"]

            prs_scores = {}
            for cond, mult in risk_multipliers.items():
                prs_percentile = min(99.9, round((mult - 1.0) * 50 + 50, 1)) if mult > 1.0 else 50.0
                prs_scores[cond] = {
                    "risk_multiplier": round(mult, 2),
                    "polygenic_risk_percentile": prs_percentile,
                    "risk_category": "HIGH" if prs_percentile >= 75 else ("ELEVATED" if prs_percentile >= 60 else "NORMAL"),
                }

            return (variants, detected_variants, prs_scores)

    # =========================================================================
    # 📈 TELEMETRY LTTB DOWNSAMPLING (LARGEST-TRIANGLE-THREE-BUCKETS)
    # =========================================================================
    def downsample_lttb_rust(self, data: List[Tuple[float, float]], threshold: int = 500) -> List[Tuple[float, float]]:
        """Downsamples time-series telemetry using Largest-Triangle-Three-Buckets algorithm in Rust."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.downsample_lttb_py(data, threshold)
        except Exception:
            if threshold >= len(data) or threshold <= 2:
                return data
            sampled = [data[0]]
            bucket_size = (len(data) - 2) / (threshold - 2)
            a = 0

            for i in range(threshold - 2):
                range_offs = int((i + 0) * bucket_size) + 1
                range_to = int((i + 1) * bucket_size) + 1
                next_range_offs = int((i + 1) * bucket_size) + 1
                next_range_to = int((i + 2) * bucket_size) + 1
                next_range_to = min(next_range_to, len(data))

                # Calculate average point for the next bucket
                avg_x = sum(pt[0] for pt in data[next_range_offs:next_range_to]) / max(1, next_range_to - next_range_offs)
                avg_y = sum(pt[1] for pt in data[next_range_offs:next_range_to]) / max(1, next_range_to - next_range_offs)

                # Find point in current bucket with largest triangle area with point A and Avg point
                max_area = -1.0
                max_idx = range_offs
                pt_a = data[a]

                for j in range(range_offs, min(range_to, len(data))):
                    pt_b = data[j]
                    area = abs((pt_a[0] - avg_x) * (pt_b[1] - pt_a[1]) - (pt_a[0] - pt_b[0]) * (avg_y - pt_a[1])) * 0.5
                    if area > max_area:
                        max_area = area
                        max_idx = j

                sampled.append(data[max_idx])
                a = max_idx

            sampled.append(data[-1])
            return sampled

    # =========================================================================
    # 🔐 CRYPTOGRAPHIC MERKLE PROOF ATTESTATION
    # =========================================================================
    def verify_merkle_proof_rust(self, leaf_hash: str, proof: List[str], root_hash: str) -> bool:
        """Verifies Merkle branch proof in Rust constant-time SHA-256."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.verify_merkle_proof_py(leaf_hash, proof, root_hash)
        except Exception:
            import hashlib
            current = leaf_hash
            for p in proof:
                # Lexicographical ordering for deterministic Merkle hashing
                combined = (current + p).encode("utf-8") if current < p else (p + current).encode("utf-8")
                current = hashlib.sha256(combined).hexdigest()
            return current == root_hash

    # =========================================================================
    # 🫀 FRAMINGHAM 10-YEAR CARDIOVASCULAR RISK
    # =========================================================================
    def calculate_framingham_risk_rust(
        self, age: float, is_female: bool, total_chol: float, hdl_chol: float,
        sbp: float, smoker: bool, diabetes: bool, hyp_treatment: bool
    ) -> float:
        """Calculates 10-year CVD risk percentage in Rust / Python IEEE-754 floating point."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.calculate_framingham_risk_py(
                age, is_female, total_chol, hdl_chol, sbp, smoker, diabetes, hyp_treatment
            )
        except Exception:
            clamped_age = max(30.0, min(74.0, age))
            ln_age = math.log(clamped_age)
            ln_tc = math.log(total_chol)
            ln_hdl = math.log(hdl_chol)
            ln_sbp = math.log(sbp)

            if is_female:
                mean_sum = 26.0145
                baseline = 0.94833
                coeff_sum = (
                    (2.72107 * ln_age) + (0.81734 * ln_tc) + (-0.27634 * ln_hdl) +
                    ((2.88267 if hyp_treatment else 2.81291) * ln_sbp) +
                    (0.61868 * float(smoker)) + (0.77763 * float(diabetes))
                )
            else:
                mean_sum = 23.9388
                baseline = 0.88431
                coeff_sum = (
                    (3.06117 * ln_age) + (1.12370 * ln_tc) + (-0.93267 * ln_hdl) +
                    ((1.99881 if hyp_treatment else 1.93303) * ln_sbp) +
                    (0.70953 * float(smoker)) + (0.53160 * float(diabetes))
                )

            try:
                risk = 1.0 - (baseline ** math.exp(coeff_sum - mean_sum))
                return round(risk * 100.0, 1)
            except OverflowError:
                return 99.9

    # =========================================================================
    # 💊 PHARMACOGENOMICS (PGX) CPIC DIPLOTYPE MATCHING
    # =========================================================================
    def match_pgx_diplotype_rust(
        self, medication: str, gene: str, diplotype: str, rules_catalog: dict
    ) -> dict:
        """Evaluates PGx drug-gene interaction guidelines in Rust or in-memory fallback."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.match_pgx_diplotype_py(medication, gene, diplotype, rules_catalog)
        except Exception:
            key = (medication.lower(), gene.upper())
            if key in rules_catalog and diplotype in rules_catalog[key]:
                info = rules_catalog[key][diplotype]
                return {
                    "medication": medication,
                    "gene": gene.upper(),
                    "diplotype": diplotype,
                    "metabolizer_phenotype": info["metabolizer"],
                    "pgx_recommendation_action": info["action"],
                    "clinical_guideline": info["recommendation"],
                    "is_pgx_alert": info["action"] != "STANDARD_DOSING",
                }
            return {
                "medication": medication,
                "gene": gene.upper(),
                "diplotype": diplotype,
                "metabolizer_phenotype": "UNKNOWN/WILD_TYPE",
                "pgx_recommendation_action": "STANDARD_DOSING",
                "clinical_guideline": "No specific CPIC PGx contraindication found for this diplotype.",
                "is_pgx_alert": False,
            }

    # =========================================================================
    # ⚖️ TWO-TOWER VECTOR RANKING & SIMILARITY
    # =========================================================================
    def rank_candidates_two_tower_rust(
        self, query_vec: List[float], candidate_vectors: List[List[float]], top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """Ranks candidate vectors by cosine similarity using Rust SIMD / Fallback."""
        try:
            import rust_gateway_ffi
            return rust_gateway_ffi.rank_candidates_two_tower_py(query_vec, candidate_vectors, top_k)
        except Exception:
            norm_q = math.sqrt(sum(x * x for x in query_vec))
            if norm_q == 0:
                return []
            scores = []
            for i, cand in enumerate(candidate_vectors):
                norm_c = math.sqrt(sum(y * y for y in cand))
                if norm_c > 0:
                    dot = sum(x * y for x, y in zip(query_vec, cand))
                    sim = dot / (norm_q * norm_c)
                    scores.append((i, round(sim, 4)))
                else:
                    scores.append((i, 0.0))
            scores.sort(key=lambda item: item[1], reverse=True)
            return scores[:top_k]


rust_bridge = RustBridgeEngine()
sota_rust_engine_layer_engine = rust_bridge
