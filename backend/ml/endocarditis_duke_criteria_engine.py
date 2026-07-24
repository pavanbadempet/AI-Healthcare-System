"""
Infective Endocarditis Modified Duke Criteria Diagnostic Classifier Engine
============================================================================
Evaluates 2023 Modified Duke Criteria: Major criteria (blood cultures, echo vegetation/abscess/PET-CT)
and Minor criteria (predisposition, fever, vascular Janeway, immunologic Osler/Roth) for Definite vs Possible IE.
"""

from typing import Dict


class EndocarditisDukeCriteriaEngine:
    """Evaluates 2023 Modified Duke Criteria for Infective Endocarditis diagnosis."""

    def evaluate_duke_criteria(
        self,
        major_blood_culture_positive: bool = True,  # Typical IE organisms (S. aureus, Viridans, Enterococcus)
        major_echo_or_pet_positive: bool = True,  # Vegetation, abscess, new valve regurgitation
        minor_predisposing_heart_condition_or_ivdu: bool = False,
        minor_fever_over_38c: bool = False,
        minor_vascular_phenomena: bool = False,  # Janeway lesions, emboli, mycotic aneurysm
        minor_immunologic_phenomena: bool = False,  # Osler nodes, Roth spots, glomerulonephritis
        minor_microbiologic_evidence: bool = False,  # Culture positive not meeting major
    ) -> Dict[str, any]:
        major_count = sum([major_blood_culture_positive, major_echo_or_pet_positive])

        minor_count = sum([
            minor_predisposing_heart_condition_or_ivdu,
            minor_fever_over_38c,
            minor_vascular_phenomena,
            minor_immunologic_phenomena,
            minor_microbiologic_evidence,
        ])

        duke_classification = "REJECTED_INFECTIVE_ENDOCARDITIS"
        empiric_antibiotics_indicated = False

        if major_count >= 2 or (major_count == 1 and minor_count >= 3) or (minor_count >= 5):
            duke_classification = "DEFINITE_INFECTIVE_ENDOCARDITIS"
            empiric_antibiotics_indicated = True
        elif (major_count == 1 and minor_count >= 1) or (minor_count >= 3):
            duke_classification = "POSSIBLE_INFECTIVE_ENDOCARDITIS"
            empiric_antibiotics_indicated = True

        recommendation = "Criteria for Infective Endocarditis not met; evaluate alternative etiologies of fever/bacteremia"
        if duke_classification == "DEFINITE_INFECTIVE_ENDOCARDITIS":
            recommendation = f"DEFINITE INFECTIVE ENDOCARDITIS ({major_count} Major, {minor_count} Minor criteria met): Initiate targeted IV bactericidal antibiotic therapy (e.g., Vancomycin + Cefepime empiric, or culture-directed) for 4-6 weeks; serial TEE at 7 days"
        elif duke_classification == "POSSIBLE_INFECTIVE_ENDOCARDITIS":
            recommendation = f"POSSIBLE INFECTIVE ENDOCARDITIS ({major_count} Major, {minor_count} Minor criteria met): Obtain repeat blood cultures Q12H x 3 sets, perform transesophageal echocardiogram (TEE), and maintain empiric IV coverage"

        return {
            "major_criteria_count": major_count,
            "minor_criteria_count": minor_count,
            "duke_classification": duke_classification,
            "empiric_antibiotics_indicated": empiric_antibiotics_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
duke_engine = EndocarditisDukeCriteriaEngine()
