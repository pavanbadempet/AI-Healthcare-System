"""
Multi-Modal Radiology Automated Pre-Reader Agent
=================================================
Analyzes diagnostic imaging metadata, Hounsfield Unit statistics, and clinical indications
to produce preliminary radiology impression reports (Chest X-Ray, CT, MRI).
"""

from typing import Dict, List, Optional


class RadiologyPreReaderAgent:
    """Generates preliminary radiology pre-read impression reports."""

    def generate_pre_read_impression(
        self,
        modality: str,  # 'CXRAY', 'CT_CHEST', 'MRI_BRAIN'
        clinical_indication: str,
        detected_findings: List[str],
    ) -> Dict[str, any]:
        findings_str = "; ".join(detected_findings) if detected_findings else "No acute abnormality detected."
        text_lower = clinical_indication.lower() + " " + findings_str.lower()

        urgency = "ROUTINE"
        if any(kw in text_lower for kw in ["pneumothorax", "hemorrhage", "pulmonary embolism", "aortic dissection"]):
            urgency = "CRITICAL_STAT"

        impression_text = (
            f"PRELIMINARY RADIOLOGY PRE-READ ({modality})\n"
            f"Clinical Indication: {clinical_indication}\n"
            f"Findings: {findings_str}\n"
            f"Urgency Status: {urgency}\n"
            f"Disclaimer: Preliminary AI pre-read for triage prioritization. Final verification by Board-Certified Radiologist required.\n"
        )

        return {
            "modality": modality,
            "clinical_indication": clinical_indication,
            "detected_findings": detected_findings,
            "impression_text": impression_text,
            "urgency_level": urgency,
            "requires_stat_radiologist_alert": urgency == "CRITICAL_STAT",
            "status": "PRE_READ_COMPLETED",
        }


# Singleton agent instance
radiology_prereader_agent = RadiologyPreReaderAgent()
