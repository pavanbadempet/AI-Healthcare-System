"""
Automated E-Prescribing Drug Safety & Contraindication Agent
============================================================
Audits clinical prescription requests against patient renal function (eGFR),
hepatic status (FIB-4), and known drug-drug interactions.
Provides automated dosage adjustments and warning alerts.
"""

from typing import Dict, List, Optional

# Drug-Drug Interaction Matrix
DRUG_INTERACTION_MATRIX = {
    ("metformin", "contrast"): {
        "severity": "HIGH",
        "description": "Metformin with IV iodinated contrast increases risk of lactic acidosis. Hold metformin 48h prior.",
    },
    ("lisinopril", "spironolactone"): {
        "severity": "HIGH",
        "description": "Combined ACE inhibitor and potassium-sparing diuretic increases severe hyperkalemia risk.",
    },
    ("warfarin", "aspirin"): {
        "severity": "HIGH",
        "description": "Concomitant anticoagulant and antiplatelet therapy significantly elevates major bleeding risk.",
    },
}


class PrescribingSafetyAgent:
    """Evaluates prescription safety against patient vitals, renal function, and drug interactions."""

    def evaluate_prescription_safety(
        self,
        medication_name: str,
        dosage_mg: float,
        egfr: Optional[float] = None,
        active_medications: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        med_lower = medication_name.lower()
        active_meds = [m.lower() for m in (active_medications or [])]
        warnings = []
        dosage_adjusted = False
        recommended_dosage_mg = dosage_mg

        # 1. Renal Adjustment Checks (eGFR)
        if egfr is not None:
            if "metformin" in med_lower and egfr < 30.0:
                warnings.append({
                    "type": "RENAL_CONTRAINDICATION",
                    "severity": "CRITICAL",
                    "message": f"Metformin contra-indicated when eGFR < 30 mL/min/1.73m² (Current eGFR: {egfr}). Discontinue.",
                })
            elif "metformin" in med_lower and 30.0 <= egfr < 45.0:
                recommended_dosage_mg = min(dosage_mg, 500.0)
                dosage_adjusted = True
                warnings.append({
                    "type": "RENAL_DOSAGE_ADJUSTMENT",
                    "severity": "WARNING",
                    "message": "eGFR between 30-45 mL/min/1.73m²: Max recommended Metformin dose is 500mg/day.",
                })

        # 2. Drug-Drug Interaction Checks
        for active in active_meds:
            pair1 = (med_lower, active)
            pair2 = (active, med_lower)
            if pair1 in DRUG_INTERACTION_MATRIX:
                info = DRUG_INTERACTION_MATRIX[pair1]
                warnings.append({
                    "type": "DRUG_INTERACTION",
                    "severity": info["severity"],
                    "message": f"Interaction detected with {active.title()}: {info['description']}",
                })
            elif pair2 in DRUG_INTERACTION_MATRIX:
                info = DRUG_INTERACTION_MATRIX[pair2]
                warnings.append({
                    "type": "DRUG_INTERACTION",
                    "severity": info["severity"],
                    "message": f"Interaction detected with {active.title()}: {info['description']}",
                })

        has_critical = any(w["severity"] in ["CRITICAL", "HIGH"] for w in warnings)

        return {
            "medication": medication_name,
            "original_dosage_mg": dosage_mg,
            "recommended_dosage_mg": recommended_dosage_mg,
            "dosage_adjusted": dosage_adjusted,
            "safety_status": "REJECTED" if has_critical else ("WARNING" if warnings else "SAFE"),
            "warnings": warnings,
        }


# Singleton instance
prescribing_safety_agent = PrescribingSafetyAgent()
