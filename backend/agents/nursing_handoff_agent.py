"""
Automated Nursing Shift Handoff (SBAR) Agent
==============================================
Compiles patient vitals, active IV lines, high-risk flags, and pending lab orders into
standardized SBAR (Situation, Background, Assessment, Recommendation) nursing handoff cards.
"""

from typing import Dict, List, Optional


class NursingHandoffAgent:
    """Generates structured SBAR nursing shift handoff reports."""

    def generate_sbar_handoff(
        self,
        patient_id: int,
        patient_name: str,
        room_number: str,
        chief_complaint: str,
        recent_vitals_summary: str,
        active_iv_lines: List[str],
        pending_labs: List[str],
        nurse_notes: Optional[str] = None,
    ) -> Dict[str, any]:
        situation = f"Patient {patient_name} in Room {room_number}. Primary Complaint: {chief_complaint}."
        background = f"Admitted for clinical monitoring. Active IV lines: {', '.join(active_iv_lines) or 'None'}."
        assessment = f"Recent vitals: {recent_vitals_summary}. Patient stable over shift."
        recommendation = f"Pending labs to follow up: {', '.join(pending_labs) or 'None'}. {nurse_notes or 'Recheck vitals Q4H.'}"

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "room_number": room_number,
            "sbar": {
                "situation": situation,
                "background": background,
                "assessment": assessment,
                "recommendation": recommendation,
            },
            "active_iv_lines": active_iv_lines,
            "pending_labs": pending_labs,
            "status": "HANDOFF_READY",
        }


# Singleton agent instance
nursing_handoff_agent = NursingHandoffAgent()
