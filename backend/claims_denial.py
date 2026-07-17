import json
import os
from typing import Any, Dict, List

from backend.claims import CMS1500Claim


def load_billing_rules() -> dict:
    """Loads billing guidelines from dynamic JSON contract database, falling back to static patterns."""
    fallback = {
        "cpt_diagnosis_rules": {
            "90837": {"prefix": "F", "message": "Psychotherapy requires a behavioral health diagnosis (e.g., F32.x, F41.x)"},
            "90791": {"prefix": "F", "message": "Psychiatric diagnostic evaluation requires a behavioral health diagnosis"},
            "50200": {"prefix": "N", "message": "Renal biopsy requires a genitourinary / renal diagnosis (e.g., N18.x)"},
            "90935": {"prefix": "N", "message": "Hemodialysis requires a genitourinary / renal diagnosis (e.g., N18.x)"},
            "93000": {"prefix": "I", "message": "Electrocardiogram requires a circulatory / cardiac diagnosis (e.g., I25.x)"},
            "93015": {"prefix": "I", "message": "Cardiovascular stress test requires a circulatory / cardiac diagnosis"},
            "94010": {"prefix": "J", "message": "Spirometry / lung function test requires a respiratory diagnosis (e.g., J44.x)"},
        },
        "telemedicine_rules": {
            "telehealth_places_of_service": ["02", "10"],
            "required_modifiers": ["95", "GT", "GQ"],
            "applicable_cpts": ["90837", "90791"]
        }
    }

    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "contracts", "billing_rules.json"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "contracts", "billing_rules.json")),
        "data/contracts/billing_rules.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
    return fallback

def analyse_denial_risk(claim: CMS1500Claim) -> Dict[str, Any]:
    """
    Evaluates a CMS-1500 claim against clinical coding guidelines and structural requirements
    to predict the risk of insurance claim denial.
    """
    warnings: List[str] = []
    denial_risk = "LOW"

    # 1. Structural Checks
    npi = claim.provider_npi.strip() if claim.provider_npi else ""
    if not npi or len(npi) != 10 or not npi.isdigit():
        warnings.append("Provider NPI must be exactly a 10-digit numeric value.")
        denial_risk = "HIGH"

    tax_id = claim.provider_tax_id.strip() if claim.provider_tax_id else ""
    if not tax_id:
        warnings.append("Provider Tax ID / EIN is missing.")
        denial_risk = "HIGH"

    if not claim.insurance_id or not claim.insurance_id.strip():
        warnings.append("Patient Insurance Policy ID is missing.")
        denial_risk = "HIGH"

    if not claim.diagnoses:
        warnings.append("At least one ICD-10 diagnosis code must be present on the claim.")
        denial_risk = "HIGH"

    # Load dynamic rules
    rules = load_billing_rules()
    cpt_diagnosis_rules = rules.get("cpt_diagnosis_rules", {})
    telehealth_rules = rules.get("telemedicine_rules", {})

    pos = (claim.place_of_service or "").strip()
    telehealth_pos = telehealth_rules.get("telehealth_places_of_service", ["02", "10"])
    required_mods = telehealth_rules.get("required_modifiers", ["95", "GT", "GQ"])
    applicable_cpts = telehealth_rules.get("applicable_cpts", ["90837", "90791"])
    is_telehealth = pos in telehealth_pos

    # 2. Procedure and Diagnosis Code Match Validation
    for proc in claim.procedures:
        cpt = proc.get("cpt", "").strip()
        if not cpt:
            warnings.append("Procedure service line is missing CPT/HCPCS code.")
            denial_risk = "HIGH"
            continue

        # Telehealth modifier check
        if is_telehealth and cpt in applicable_cpts:
            modifiers = proc.get("modifiers", [])
            clean_mods = [str(m).strip().upper() for m in modifiers]
            if not any(m in clean_mods for m in required_mods):
                warnings.append(
                    f"Telehealth CPT {cpt} requires a telemedicine modifier (95, GT, GQ) when billed from place of service {pos}."
                )
                if denial_risk != "HIGH":
                    denial_risk = "MEDIUM"

        rule = cpt_diagnosis_rules.get(cpt)
        if rule:
            prefix = rule.get("prefix", "")
            message = rule.get("message", "")
            # Check if any associated diagnosis code matches the prefix
            matching_dx = False
            for dx in claim.diagnoses:
                if dx.strip().upper().startswith(prefix.upper()):
                    matching_dx = True
                    break

            if not matching_dx:
                warnings.append(f"CPT {cpt} Mismatch: {message}. Claimed diagnoses: {claim.diagnoses}")
                if denial_risk != "HIGH":
                    denial_risk = "MEDIUM"

    return {
        "claim_id": claim.claim_id,
        "denial_risk": denial_risk,
        "warnings": warnings,
        "passed_preflight": len(warnings) == 0
    }

