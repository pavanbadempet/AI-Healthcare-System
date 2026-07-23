"""
Clinical Trial Eligibility Matching Agent
==========================================
Screens patient health profiles (diagnoses, lab values, genomics) against a registry
of clinical trial protocols (NCT IDs) to calculate eligibility match scores.
"""

from typing import Dict, List, Optional

CURATED_TRIAL_REGISTRY = [
    {
        "nct_id": "NCT04253123",
        "title": "Novel SGLT2 Inhibitor in Type 2 Diabetes & Chronic Kidney Disease",
        "condition": "diabetes",
        "min_age": 18,
        "max_age": 75,
        "required_icd10": ["E11.9", "N18.3"],
        "min_egfr": 30.0,
        "max_egfr": 60.0,
        "phase": "Phase III",
    },
    {
        "nct_id": "NCT05124987",
        "title": "PCSK9 Monoclonal Antibody for Early Coronary Artery Disease",
        "condition": "heart",
        "min_age": 40,
        "max_age": 80,
        "required_icd10": ["I10", "I25.10"],
        "phase": "Phase II",
    },
]


class ClinicalTrialMatchingAgent:
    """Matches patient records against clinical trials to identify recruitment candidates."""

    def match_patient_to_trials(
        self,
        age: int,
        primary_condition: str,
        egfr: Optional[float] = None,
        icd10_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, any]]:
        matches = []
        cond_lower = primary_condition.lower()
        patient_icd10 = set(icd10_codes or [])

        for trial in CURATED_TRIAL_REGISTRY:
            score = 0
            reasons = []

            # Age match
            if trial["min_age"] <= age <= trial["max_age"]:
                score += 30
                reasons.append(f"Age {age} meets inclusion range [{trial['min_age']}-{trial['max_age']}]")
            else:
                continue

            # Condition match
            if trial["condition"] in cond_lower:
                score += 40
                reasons.append(f"Condition '{trial['condition']}' matches trial protocol")

            # eGFR match
            if "min_egfr" in trial and egfr is not None:
                if trial["min_egfr"] <= egfr <= trial.get("max_egfr", 120.0):
                    score += 30
                    reasons.append(f"eGFR {egfr} satisfies renal criteria")

            # ICD-10 overlap match
            required_set = set(trial.get("required_icd10", []))
            if required_set and patient_icd10.intersection(required_set):
                score += 20
                reasons.append("Matching ICD-10 diagnostic codes identified")

            match_percentage = min(100, score)
            if match_percentage >= 50:
                matches.append({
                    "nct_id": trial["nct_id"],
                    "title": trial["title"],
                    "phase": trial["phase"],
                    "match_score": match_percentage,
                    "eligibility_reasons": reasons,
                    "status": "ELIGIBLE" if match_percentage >= 70 else "POTENTIAL",
                })

        return sorted(matches, key=lambda x: x["match_score"], reverse=True)


# Singleton agent instance
trial_matching_agent = ClinicalTrialMatchingAgent()
