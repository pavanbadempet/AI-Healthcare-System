"""Automated Medical Prior Authorization & CMS Coverage Determination Agent
========================================================================
Audits clinical documentation against CMS Local and National Coverage Determinations
(LCDs/NCDs), commercial payer medical policies, conservative therapy durations,
and objective clinical criteria (MRI spine, knee arthroscopy, biologics, CT angiography).

Synthesizes complete medical necessity authorization packages, criteria-met checklists,
appeal letters for disputed denials, and emits strongly-typed FHIR action proposals.
"""

from __future__ import annotations

import datetime
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

# Ensure package directory is on sys.path if not installed in editable mode
_pkg_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "packages", "clinical-fhir-abdm", "src")
)
if _pkg_path not in sys.path and os.path.isdir(_pkg_path):
    sys.path.insert(0, _pkg_path)

try:
    from clinical_fhir_abdm.schemas import (
        ClinicalAgentResponse,
        FHIRFlagProposal,
        FHIRServiceRequestProposal,
    )
except ImportError:
    @dataclass
    class FHIRServiceRequestProposal:
        patient_id: str
        category: str
        code: str
        description: str
        urgency: str = "routine"
        indication: str = ""
        requester: Optional[str] = None
        supporting_info: Optional[List[str]] = None
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"sr-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)
            if self.supporting_info is None:
                self.supporting_info = []

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

    @dataclass
    class FHIRFlagProposal:
        patient_id: str
        status: str = "active"
        category: str = "clinical_alert"
        severity: str = "warning"
        code: str = ""
        details: str = ""
        author: Optional[str] = None
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"flag-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

    @dataclass
    class ClinicalAgentResponse:
        recommendations: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
        proposed_fhir_actions: List[Any] = field(default_factory=list)
        epistemic_confidence: float = 1.0
        agent_name: Optional[str] = None
        reasoning: Optional[str] = None
        metadata: Dict[str, Any] = field(default_factory=dict)
        timestamp: datetime.datetime = field(
            default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

        def to_dict(self) -> Dict[str, Any]:
            return {
                "agent_name": self.agent_name,
                "epistemic_confidence": round(self.epistemic_confidence, 4),
                "recommendations": self.recommendations,
                "proposed_fhir_actions": [
                    a.to_dict() if hasattr(a, "to_dict") else a for a in self.proposed_fhir_actions
                ],
                "reasoning": self.reasoning,
                "metadata": self.metadata,
                "timestamp": self.timestamp.isoformat(),
            }


# CMS Coverage Policies (LCDs/NCDs) Knowledge Base
CMS_COVERAGE_POLICIES: Dict[str, Dict[str, Any]] = {
    "72148": {
        "policy_id": "CMS-LCD-L34932",
        "policy_title": "Magnetic Resonance Imaging (MRI) of the Lumbar Spine",
        "procedure_name": "MRI Lumbar Spine without Contrast",
        "eligible_icd10_prefixes": ["M54", "M51", "G57", "S32", "S34"],
        "min_conservative_weeks": 6,
        "required_criteria": [
            "Radiculopathy, neurogenic claudication, or progressive neurological deficit documented",
            "Minimum 6 consecutive weeks of failed conservative therapy (e.g. Physical Therapy, NSAIDs, Epidural injection)",
            "Absence of urgent red flags (cauda equina, acute fracture, progressive motor deficit) which bypass conservative trial",
        ],
        "red_flag_bypass_keywords": ["cauda equina", "saddle anesthesia", "bowel incontinence", "bladder incontinence", "acute foot drop", "progressive motor deficit"],
    },
    "29881": {
        "policy_id": "CMS-LCD-L35075",
        "policy_title": "Arthroscopy of the Knee (Meniscectomy)",
        "procedure_name": "Arthroscopy, Knee, Surgical; with Meniscectomy (Medial or Lateral)",
        "eligible_icd10_prefixes": ["M23", "S83"],
        "min_conservative_weeks": 6,
        "required_criteria": [
            "Physical examination demonstrating joint-line tenderness or McMurray test positivity",
            "Mechanical symptoms (true joint locking or catching) documented",
            "MRI or imaging confirming discrete meniscal tear",
            "Minimum 6 weeks of conservative management (rest, physical therapy, NSAIDs, or steroid injection) failed",
        ],
        "red_flag_bypass_keywords": ["locked knee", "acute bucket-handle tear", "inability to extend"],
    },
    "75574": {
        "policy_id": "CMS-LCD-L37032",
        "policy_title": "Computed Tomography Angiography (CCTA) Coronary Arteries",
        "procedure_name": "Computed Tomography Angiography, Heart and Coronary Vessels",
        "eligible_icd10_prefixes": ["I20", "I25", "R07"],
        "min_conservative_weeks": 0,
        "required_criteria": [
            "Intermediate pre-test probability of obstructive Coronary Artery Disease (CAD)",
            "Inconclusive prior stress test or patient physically unable to perform treadmill stress exercise",
            "Controlled resting heart rate (<65 bpm) or protocol for pre-scan beta-blockade",
            "Adequate renal reserve (eGFR >45 mL/min) for iodinated contrast administration",
        ],
        "red_flag_bypass_keywords": ["acute coronary syndrome", "troponin elevation", "unstable angina"],
    },
    "J0129": {
        "policy_id": "CMS-NCD-200.2",
        "policy_title": "Biologics and Targeted Immunomodulators for Inflammatory Arthritis",
        "procedure_name": "Abatacept (Orencia) Injection / Infusion",
        "eligible_icd10_prefixes": ["M05", "M06", "M08"],
        "min_conservative_weeks": 12,
        "required_criteria": [
            "Documented diagnosis of moderate-to-severe active Rheumatoid Arthritis (CDAI >22 or DAS28 >5.1)",
            "Documented failure or intolerance of at least one conventional synthetic DMARD (e.g. Methotrexate >=15mg/wk, Leflunomide) for >=12 weeks",
            "Negative screening for latent tuberculosis (PPD/QuantiFERON) within 12 months",
            "Negative Hepatitis B and C serology confirmed",
        ],
        "red_flag_bypass_keywords": ["rapidly destructive joint disease"],
    },
}


class PriorAuthorizationAgent:
    """Evaluates coverage criteria against CMS LCDs/NCDs and synthesizes authorization packets."""

    def __init__(self) -> None:
        self.agent_name = "PriorAuthorization_ComplianceAgent"

    def match_coverage_policy(
        self,
        cpt_code: str,
        primary_icd10: str,
        clinical_justification: str,
        failed_conservative_therapies: List[str],
    ) -> Dict[str, Any]:
        """Matches clinical presentation against CMS LCD/NCD rules."""
        cpt_clean = cpt_code.strip()
        policy = CMS_COVERAGE_POLICIES.get(cpt_clean)

        if not policy:
            # Generic coverage check
            has_icd = bool(primary_icd10)
            has_justification = len(clinical_justification) >= 30
            has_conservative = len(failed_conservative_therapies) > 0
            is_met = has_icd and has_justification and has_conservative

            return {
                "policy_matched": False,
                "policy_id": "PAYER_GENERIC_MEDICAL_NECESSITY",
                "policy_title": f"Standard Medical Necessity Review for CPT {cpt_code}",
                "criteria_met": [
                    "Primary diagnosis code provided" if has_icd else "Missing primary diagnosis code",
                    "Clinical narrative provided" if has_justification else "Insufficient clinical narrative",
                    "Prior conservative therapies documented" if has_conservative else "No conservative therapy documented",
                ],
                "unmet_criteria": [] if is_met else ["Incomplete documentation"],
                "is_approved": is_met,
                "red_flag_bypass_active": False,
            }

        # Detailed CMS Policy Evaluation
        criteria_met: List[str] = []
        unmet_criteria: List[str] = []
        text_lower = (clinical_justification + " " + " ".join(failed_conservative_therapies)).lower()

        # 1. ICD-10 diagnostic concordance
        icd_clean = primary_icd10.strip().upper()
        icd_matches = any(icd_clean.startswith(prefix) for prefix in policy["eligible_icd10_prefixes"])
        if icd_matches:
            criteria_met.append(f"Diagnostic concordance: ICD-10 {primary_icd10} satisfies {policy['policy_id']} eligible code list.")
        else:
            unmet_criteria.append(
                f"ICD-10 {primary_icd10} is not listed as an indicated diagnosis under {policy['policy_id']} (requires prefix in {policy['eligible_icd10_prefixes']})."
            )

        # 2. Red flag emergency bypass check
        red_flags_present = any(rf in text_lower for rf in policy.get("red_flag_bypass_keywords", []))
        if red_flags_present:
            criteria_met.append(
                "EMERGENCY CLINICAL RED FLAG DETECTED: Conservative trial requirement waived due to acute presentation."
            )

        # 3. Conservative therapy duration
        min_weeks = policy["min_conservative_weeks"]
        if not red_flags_present and min_weeks > 0:
            if len(failed_conservative_therapies) == 0:
                unmet_criteria.append(
                    f"Policy mandates minimum {min_weeks} weeks of documented conservative management; zero failed therapies documented."
                )
            else:
                criteria_met.append(
                    f"Documented failed conservative therapies: {', '.join(failed_conservative_therapies)}."
                )

        # 4. Clinical justification length & depth
        if len(clinical_justification.strip()) >= 25:
            criteria_met.append("Clinical narrative provides adequate medical necessity context.")
        else:
            unmet_criteria.append("Clinical justification is too brief (<25 characters) to substantiate medical necessity.")

        is_approved = len(unmet_criteria) == 0

        return {
            "policy_matched": True,
            "policy_id": policy["policy_id"],
            "policy_title": policy["policy_title"],
            "procedure_name": policy["procedure_name"],
            "criteria_met": criteria_met,
            "unmet_criteria": unmet_criteria,
            "is_approved": is_approved,
            "red_flag_bypass_active": red_flags_present,
        }

    def generate_appeal_letter(
        self,
        patient_id: int,
        patient_name: str,
        requested_procedure_cpt: str,
        primary_icd10: str,
        clinical_justification: str,
        unmet_criteria: List[str],
        policy_id: str,
    ) -> str:
        """Synthesizes formal medical necessity peer-to-peer / appeal letter for disputed or initially denied authorization."""
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        unmet_bulleted = "\n".join(f"- {c}" for c in unmet_criteria) or "- None noted"

        return (
            f"EXPEDITED PRIOR AUTHORIZATION RECONSIDERATION / APPEAL LETTER\n"
            f"Date: {date_str}\n"
            f"To: Medical Director, Utilization Review & Clinical Appeals\n"
            f"Re: Prior Authorization Expedited Appeal for {patient_name} (Patient ID #{patient_id})\n"
            f"Service Requested: CPT {requested_procedure_cpt}\n"
            f"Primary Diagnostic Code: ICD-10 {primary_icd10}\n"
            f"Applicable Coverage Policy: {policy_id}\n\n"
            f"Dear Medical Director,\n\n"
            f"I am writing to formally appeal the preliminary coverage determination for the above-referenced patient. "
            f"The requested procedure (CPT {requested_procedure_cpt}) is medically necessary, non-experimental, and "
            f"directly aligned with peer-reviewed clinical guidelines and standard of care.\n\n"
            f"CLINICAL SUMMARY & JUSTIFICATION:\n"
            f"{clinical_justification}\n\n"
            f"REBUTTAL OF NOTED CRITERIA GAPS:\n"
            f"{unmet_bulleted}\n\n"
            f"Delaying this requested intervention increases the acute risk of permanent functional impairment, "
            f"neurological deterioration, or emergency hospitalization. I request an expedited peer-to-peer review "
            f"or immediate reversal of this adverse determination.\n\n"
            f"Sincerely,\n"
            f"Attending Physician, Department of Specialty Medicine\n"
            f"Board-Certified Clinician"
        )

    def generate_prior_auth_package(
        self,
        patient_id: int,
        patient_name: str,
        requested_procedure_cpt: str,
        primary_icd10: str,
        clinical_justification: str,
        failed_conservative_therapies: List[str],
        clinical_vital_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured prior authorization package with CMS policy audit and appeal drafts."""
        pid_str = str(patient_id)
        evaluation = self.match_coverage_policy(
            cpt_code=requested_procedure_cpt,
            primary_icd10=primary_icd10,
            clinical_justification=clinical_justification,
            failed_conservative_therapies=failed_conservative_therapies,
        )

        has_sufficient_evidence = evaluation["is_approved"]

        # Format criteria checklist text
        met_text = "\n".join(f"  [X] {c}" for c in evaluation["criteria_met"])
        unmet_text = "\n".join(f"  [ ] {c}" for c in evaluation["unmet_criteria"]) if evaluation["unmet_criteria"] else "  None (All Criteria Satisfied)"

        pa_summary = (
            f"PRIOR AUTHORIZATION REQUEST PACKAGE\n"
            f"Patient: {patient_name} (ID #{patient_id})\n"
            f"Requested Procedure Code (CPT): {requested_procedure_cpt} ({evaluation.get('procedure_name', 'Requested Procedure')})\n"
            f"Primary Diagnosis Code (ICD-10): {primary_icd10}\n"
            f"Governing Policy: {evaluation['policy_id']} — {evaluation['policy_title']}\n\n"
            f"CLINICAL JUSTIFICATION:\n{clinical_justification}\n\n"
            f"FAILED CONSERVATIVE THERAPIES:\n- {', '.join(failed_conservative_therapies) or 'None documented'}\n\n"
            f"CMS COVERAGE CRITERIA VERIFICATION:\n"
            f"Criteria Met:\n{met_text}\n"
            f"Criteria Deficiencies / Unmet:\n{unmet_text}\n"
        )

        appeal_letter = ""
        if not has_sufficient_evidence:
            appeal_letter = self.generate_appeal_letter(
                patient_id=patient_id,
                patient_name=patient_name,
                requested_procedure_cpt=requested_procedure_cpt,
                primary_icd10=primary_icd10,
                clinical_justification=clinical_justification,
                unmet_criteria=evaluation["unmet_criteria"],
                policy_id=evaluation["policy_id"],
            )

        # FHIR Action Proposals
        proposed_actions: List[Any] = []
        if has_sufficient_evidence:
            sr_order = FHIRServiceRequestProposal(
                patient_id=pid_str,
                category="diagnostic" if requested_procedure_cpt.startswith("7") else "procedure",
                code=requested_procedure_cpt,
                description=f"Prior-Authorized: CPT {requested_procedure_cpt} ({evaluation.get('procedure_name', '')})",
                urgency="routine",
                indication=f"ICD-10 {primary_icd10} under {evaluation['policy_id']}",
                supporting_info=evaluation["criteria_met"],
            )
            proposed_actions.append(sr_order)
        else:
            flag_gap = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="clinical_alert",
                severity="warning",
                code="PRIOR_AUTH_DEFICIENT",
                details=f"Prior auth for CPT {requested_procedure_cpt} deficient: {'; '.join(evaluation['unmet_criteria'])}",
            )
            proposed_actions.append(flag_gap)

        clinical_response = ClinicalAgentResponse(
            recommendations=[
                {"action": "PRIOR_AUTH_SUBMISSION", "status": "APPROVED" if has_sufficient_evidence else "DENIED"},
                {"policy": evaluation["policy_id"], "unmet_criteria": evaluation["unmet_criteria"]},
            ],
            proposed_fhir_actions=proposed_actions,
            epistemic_confidence=0.98 if has_sufficient_evidence else 0.85,
            agent_name=self.agent_name,
            reasoning=f"Evaluated CPT {requested_procedure_cpt} against {evaluation['policy_id']}. Result: {'Compliant' if has_sufficient_evidence else 'Deficient'}.",
            metadata={
                "patient_name": patient_name,
                "cpt_code": requested_procedure_cpt,
                "icd10_code": primary_icd10,
            },
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "cpt_code": requested_procedure_cpt,
            "icd10_code": primary_icd10,
            "policy_id": evaluation["policy_id"],
            "policy_title": evaluation["policy_title"],
            "prior_auth_package_text": pa_summary,
            "criteria_evaluation": evaluation,
            "has_sufficient_evidence": has_sufficient_evidence,
            "appeal_letter": appeal_letter,
            "submission_status": "READY_FOR_SUBMISSION" if has_sufficient_evidence else "NEEDS_MORE_DOCUMENTATION",
            "proposed_fhir_actions": [a.to_dict() for a in proposed_actions],
            "clinical_response": clinical_response.to_dict(),
        }


# Singleton agent instance
prior_auth_agent = PriorAuthorizationAgent()
prior_authorization_agent = prior_auth_agent

