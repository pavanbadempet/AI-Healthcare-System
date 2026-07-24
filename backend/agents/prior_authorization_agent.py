"""
Automated Medical Prior Authorization Generator Agent
======================================================
Compiles clinical indication notes, lab results, failed conservative therapies,
and insurance payer criteria into pre-formatted Prior Authorization packages.
"""

from typing import Dict, List


class PriorAuthorizationAgent:
    """Generates prior authorization request packages for insurance pre-approval."""

    def generate_prior_auth_package(
        self,
        patient_id: int,
        patient_name: str,
        requested_procedure_cpt: str,
        primary_icd10: str,
        clinical_justification: str,
        failed_conservative_therapies: List[str],
    ) -> Dict[str, any]:
        pa_summary = (
            f"PRIOR AUTHORIZATION REQUEST PACKAGE\n"
            f"Patient: {patient_name} (ID #{patient_id})\n"
            f"Requested Procedure Code (CPT): {requested_procedure_cpt}\n"
            f"Primary Diagnosis Code (ICD-10): {primary_icd10}\n\n"
            f"CLINICAL JUSTIFICATION:\n"
            f"{clinical_justification}\n\n"
            f"FAILED CONSERVATIVE THERAPIES:\n"
            f"- {', '.join(failed_conservative_therapies) or 'None documented'}\n"
        )

        has_sufficient_evidence = len(failed_conservative_therapies) > 0 and len(clinical_justification) >= 20

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "cpt_code": requested_procedure_cpt,
            "icd10_code": primary_icd10,
            "prior_auth_package_text": pa_summary,
            "has_sufficient_evidence": has_sufficient_evidence,
            "submission_status": "READY_FOR_SUBMISSION" if has_sufficient_evidence else "NEEDS_MORE_DOCUMENTATION",
        }


# Singleton agent instance
prior_auth_agent = PriorAuthorizationAgent()
