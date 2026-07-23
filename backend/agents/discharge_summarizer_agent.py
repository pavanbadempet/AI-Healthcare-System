"""
Clinical Discharge Summarizer Agent
====================================
Compiles inpatient hospital encounter data, lab trends, active prescriptions,
red-flag warning signs, and follow-up care plans into structured clinical summaries.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class DischargeSummarizerAgent:
    """Generates comprehensive, HIPAA-oriented patient discharge summaries."""

    def generate_discharge_summary(
        self,
        patient_id: int,
        patient_name: str,
        admission_date: str,
        discharge_date: str,
        primary_diagnosis: str,
        discharge_medications: List[str],
        followup_days: int = 7,
    ) -> Dict[str, any]:
        summary_text = (
            f"PATIENT DISCHARGE SUMMARY\n"
            f"Patient: {patient_name} (ID: #{patient_id})\n"
            f"Admission: {admission_date} | Discharge: {discharge_date}\n"
            f"Primary Diagnosis: {primary_diagnosis}\n\n"
            f"DISCHARGE INSTRUCTIONS:\n"
            f"1. Take prescribed medications exactly as directed: {', '.join(discharge_medications)}.\n"
            f"2. Follow up with primary care physician within {followup_days} days.\n"
            f"3. Seek emergency care immediately if experiencing severe chest pain, shortness of breath, or high fever (>101F).\n"
        )

        fhir_document_reference = {
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "18842-5",
                        "display": "Discharge summary",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}", "display": patient_name},
            "date": datetime.now(timezone.utc).isoformat(),
            "description": f"Hospital discharge summary for {primary_diagnosis}",
        }

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "admission_date": admission_date,
            "discharge_date": discharge_date,
            "primary_diagnosis": primary_diagnosis,
            "discharge_summary_text": summary_text,
            "fhir_document_reference": fhir_document_reference,
            "red_flag_warnings": [
                "Severe chest pain or pressure",
                "Shortness of breath at rest",
                "Uncontrolled high fever > 101F",
                "Sudden weakness or numbness",
            ],
            "followup_timeline_days": followup_days,
            "status": "COMPLETED",
        }


# Singleton agent instance
discharge_summarizer = DischargeSummarizerAgent()
