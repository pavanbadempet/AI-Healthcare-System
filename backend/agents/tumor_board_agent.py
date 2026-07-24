"""
Multi-Disciplinary Team (MDT) Tumor Board Case Summarizer Agent
================================================================
Synthesizes oncology staging (TNM), pathology reports, genomic alterations (EGFR, ALK, KRAS),
and NCCN clinical guidelines into multi-disciplinary tumor board presentation cards.
"""

from typing import Dict, List, Optional


class TumorBoardAgent:
    """Generates structured multi-disciplinary tumor board briefing summaries."""

    def generate_tumor_board_summary(
        self,
        patient_id: int,
        patient_name: str,
        cancer_type: str,
        tnm_stage: str,
        pathology_summary: str,
        genomic_biomarkers: Dict[str, str],
        prior_therapies: List[str],
    ) -> Dict[str, any]:
        biomarker_str = ", ".join(f"{k}: {v}" for k, v in genomic_biomarkers.items()) or "None detected"

        summary_card = (
            f"MULTI-DISCIPLINARY TUMOR BOARD BRIEFING\n"
            f"Patient: {patient_name} (ID #{patient_id})\n"
            f"Cancer Diagnosis: {cancer_type} (Stage: {tnm_stage})\n\n"
            f"PATHOLOGY SUMMARY:\n{pathology_summary}\n\n"
            f"GENOMIC BIOMARKERS:\n{biomarker_str}\n\n"
            f"PRIOR THERAPIES:\n- {', '.join(prior_therapies) or 'None'}\n"
        )

        has_actionable_target = any(
            v.lower() in ["mutated", "positive", "amplified"] for v in genomic_biomarkers.values()
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "cancer_type": cancer_type,
            "tnm_stage": tnm_stage,
            "summary_card": summary_card,
            "has_actionable_genomic_target": has_actionable_target,
            "board_review_status": "READY_FOR_MDT_PRESENTATION",
        }


# Singleton agent instance
tumor_board_agent = TumorBoardAgent()
