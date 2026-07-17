import logging
from typing import Any, Dict

from backend.core_ai import chat

logger = logging.getLogger(__name__)

ICD10_MAPPING = {
    "diabetes": ("E11.9", "Type 2 diabetes mellitus without complications"),
    "heart": ("I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris"),
    "liver": ("K76.9", "Liver disease, unspecified"),
    "kidney": ("N18.9", "Chronic kidney disease, unspecified"),
    "lungs": ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
    "stroke": ("I63.9", "Cerebral infarction, unspecified")
}

SNOMED_MAPPING = {
    "diabetes": ("44054006", "Type 2 diabetes mellitus"),
    "heart": ("53741008", "Coronary arteriosclerosis"),
    "liver": ("328383001", "Chronic liver disease"),
    "kidney": ("709044004", "Chronic kidney disease"),
    "lungs": ("13645005", "Chronic obstructive lung disease"),
    "stroke": ("230690007", "Cerebrovascular accident")
}

async def compile_clinical_note(transcript: str, format_type: str = "SOAP") -> Dict[str, Any]:
    """
    Compiles raw transcript/symptoms into standard SOAP or DAP clinical markdown.
    """
    if format_type.upper() == "DAP":
        system_prompt = (
            "You are an expert clinical documentation assistant. Summarize the following session into a DAP note "
            "(Data, Assessment, Plan) in clear markdown format. Use concise, objective clinical language."
        )
    else:
        system_prompt = (
            "You are an expert clinical documentation assistant. Summarize the following session into a SOAP note "
            "(Subjective, Objective, Assessment, Plan) in clear markdown format. Use concise, objective clinical language."
        )

    compiled_text = await chat([{"role": "user", "content": f"Transcript:\n{transcript}"}], system=system_prompt)

    detected_codes = []
    text_lower = (compiled_text or "").lower() + " " + transcript.lower()
    for disease, (icd_code, icd_desc) in ICD10_MAPPING.items():
        if disease in text_lower or (disease == "lungs" and "respiratory" in text_lower):
            snomed_code, snomed_desc = SNOMED_MAPPING[disease]
            detected_codes.append({
                "condition": disease,
                "icd10": {"code": icd_code, "display": icd_desc},
                "snomed": {"code": snomed_code, "display": snomed_desc}
            })

    return {
        "format": format_type.upper(),
        "note_markdown": compiled_text,
        "coded_diagnoses": detected_codes
    }
