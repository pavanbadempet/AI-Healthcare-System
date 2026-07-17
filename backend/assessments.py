import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.fhir import fhir_datetime

logger = logging.getLogger(__name__)

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead or of hurting yourself in some way"
]

GAD7_QUESTIONS = [
    "Feeling nervous, anxious or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it is hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen"
]

def score_assessment(responses: List[int], questionnaire_type: str = "PHQ-9") -> Dict[str, Any]:
    """
    Scores standard clinical questionnaires (PHQ-9 or GAD-7).
    Responses must be integers in [0, 3].
    """
    questionnaire_type = questionnaire_type.upper()
    expected_len = 9 if questionnaire_type == "PHQ-9" else 7

    if len(responses) != expected_len:
        raise ValueError(f"Expected exactly {expected_len} responses for {questionnaire_type}, got {len(responses)}")

    for r in responses:
        if not (0 <= r <= 3):
            raise ValueError("All responses must be integers between 0 and 3")

    total_score = sum(responses)

    if questionnaire_type == "PHQ-9":
        if total_score <= 4:
            severity = "Minimal or None"
            recommendation = "No active clinical intervention required. Retest periodically if symptoms persist."
        elif total_score <= 9:
            severity = "Mild Depression"
            recommendation = "Clinical monitoring and support. Consider counseling/psychoeducation."
        elif total_score <= 14:
            severity = "Moderate Depression"
            recommendation = "Formulate treatment plan. Recommend psychotherapy or pharmacotherapy."
        elif total_score <= 19:
            severity = "Moderately Severe Depression"
            recommendation = "Active pharmacotherapy and/or psychotherapy recommended."
        else:
            severity = "Severe Depression"
            recommendation = "Immediate clinical intervention and specialized referral required."
    else:  # GAD-7
        if total_score <= 4:
            severity = "Minimal Anxiety"
            recommendation = "No active clinical intervention required."
        elif total_score <= 9:
            severity = "Mild Anxiety"
            recommendation = "Supportive counseling and active monitoring."
        elif total_score <= 14:
            severity = "Moderate Anxiety"
            recommendation = "Further clinical evaluation. Formulation of care plan recommended."
        else:
            severity = "Severe Anxiety"
            recommendation = "Pharmacotherapy and active psychotherapy referral recommended."

    return {
        "questionnaire": questionnaire_type,
        "score": total_score,
        "severity": severity,
        "recommendation": recommendation
    }

def to_fhir_observation(patient_id: str, score: int, severity: str, questionnaire_type: str = "PHQ-9") -> Dict[str, Any]:
    """
    Translates a scored assessment into a standard FHIR R4 Observation resource.
    """
    questionnaire_type = questionnaire_type.upper()
    loinc_code = "44249-1" if questionnaire_type == "PHQ-9" else "69737-5"
    loinc_display = "PHQ-9 Patient Depression Questionnaire" if questionnaire_type == "PHQ-9" else "GAD-7 Patient Anxiety Questionnaire"

    return {
        "resourceType": "Observation",
        "id": f"obs-{questionnaire_type.lower()}-{int(datetime.now(timezone.utc).timestamp())}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                        "display": "Survey"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": loinc_display
                }
            ],
            "text": loinc_display
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": fhir_datetime(datetime.now(timezone.utc)),
        "valueQuantity": {
            "value": float(score),
            "unit": "Score",
            "system": "http://unitsofmeasure.org",
            "code": "{score}"
        },
        "interpretation": [
            {
                "text": severity
            }
        ]
    }
