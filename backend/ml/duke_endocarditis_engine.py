"""
Infective Endocarditis Duke Criteria & Mortality Engine
======================================================
Evaluates Modified Duke Criteria (Major & Minor) to classify Definite vs Possible Infective Endocarditis.
"""

from typing import Dict


class DukeEndocarditisEngine:
    """Evaluates Modified Duke Criteria for Infective Endocarditis."""

    def evaluate_duke_criteria(
        self,
        major_blood_culture_positive: bool,
        major_echo_vegetation_or_abscess: bool,
        minor_predisposing_heart_condition: bool = False,
        minor_fever_over_38C: bool = False,
        minor_vascular_phenomena: bool = False,
        minor_immunologic_phenomena: bool = False,
        minor_microbiologic_evidence: bool = False,
    ) -> Dict[str, any]:
        major_count = sum([major_blood_culture_positive, major_echo_vegetation_or_abscess])
        minor_count = sum([
            minor_predisposing_heart_condition,
            minor_fever_over_38C,
            minor_vascular_phenomena,
            minor_immunologic_phenomena,
            minor_microbiologic_evidence,
        ])

        classification = "REJECTED_ENDOCARDITIS"
        if major_count == 2 or (major_count == 1 and minor_count >= 3) or minor_count == 5:
            classification = "DEFINITE_ENDOCARDITIS"
        elif major_count == 1 and minor_count >= 1 or minor_count >= 3:
            classification = "POSSIBLE_ENDOCARDITIS"

        recommendation = "Low suspicion; consider alternative fever etiologies"
        if classification == "DEFINITE_ENDOCARDITIS":
            recommendation = "Stat IV bactericidal antibiotic therapy & urgent Cardiology / Cardiothoracic Surgery consult"
        elif classification == "POSSIBLE_ENDOCARDITIS":
            recommendation = "Repeat TEE (Transesophageal Echocardiogram) in 3-5 days & serial blood cultures"

        return {
            "major_criteria_met_count": major_count,
            "minor_criteria_met_count": minor_count,
            "duke_classification": classification,
            "clinical_recommendation": recommendation,
            "empiric_iv_antibiotics_indicated": classification in ["DEFINITE_ENDOCARDITIS", "POSSIBLE_ENDOCARDITIS"],
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
duke_endocarditis_engine = DukeEndocarditisEngine()
