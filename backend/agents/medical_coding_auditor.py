"""Medical Coding & Revenue Integrity Auditor Agent
===================================================
Audits inpatient and outpatient clinical documentation against assigned ICD-10-CM
diagnosis codes and CPT/HCPCS procedure codes.

Performs:
1. CMS National Correct Coding Initiative (NCCI) Column 1 / Column 2 unbundling edit checks
   and Modifier 59 / X{EPSU} (XE, XP, XS, XU) appropriateness validation.
2. 2023 AMA Medical Decision Making (MDM) E/M code complexity scoring across:
   - Number and complexity of problems addressed (Minimal, Low, Moderate, High)
   - Amount and/or complexity of data to be reviewed and analyzed (Minimal, Limited, Moderate, Extensive)
   - Risk of complications and/or morbidity or mortality of patient management (Minimal, Low, Moderate, High)
   Determining appropriate E/M code levels (99202-99205, 99211-99215).
3. Inpatient MS-DRG (Medicare Severity Diagnosis Related Groups) assignment, relative weight
   tracking, Major Complication/Comorbidity (MCC) / CC impact analysis, and estimated reimbursement impact.
4. Upcoding, undercoding, and documentation deficiency detection with automated compliance findings.

Emits strongly-typed FHIR R4 action proposals (ServiceRequest, Flag) and ClinicalAgentResponse.
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


# CMS National Correct Coding Initiative (NCCI) Procedure-to-Procedure (PTP) Edits Table
# Column 1 (Comprehensive) vs Column 2 (Component). Modifier Indicator: 0 = Not Allowed, 1 = Allowed with modifier
NCCI_PTP_EDITS: List[Dict[str, Any]] = [
    {
        "col1": "45385",  # Colonoscopy with lesion removal by snare
        "col2": "45380",  # Colonoscopy with biopsy (single or multiple)
        "description": "Colonoscopy snare polypectomy includes diagnostic biopsy if performed on the same polyp/lesion.",
        "modifier_indicator": 1,  # Allowed only if separate anatomical lesions / separate sessions
        "policy_rationale": "Standards of medical/surgical practice: diagnostic biopsy prior to complete excision of same lesion is integral.",
    },
    {
        "col1": "43239",  # EGD with biopsy
        "col2": "43235",  # Diagnostic EGD
        "description": "Diagnostic EGD is inherently bundled into therapeutic/biopsy EGD.",
        "modifier_indicator": 0,  # Never unbundle on same operative encounter
        "policy_rationale": "Mutually exclusive / comprehensive code bundle; diagnostic endoscopy is baseline component.",
    },
    {
        "col1": "29881",  # Knee arthroscopy with meniscectomy
        "col2": "29870",  # Diagnostic knee arthroscopy
        "description": "Diagnostic knee arthroscopy is bundled into surgical meniscectomy.",
        "modifier_indicator": 0,
        "policy_rationale": "Surgical arthroscopy includes diagnostic inspection of the joint space.",
    },
    {
        "col1": "93458",  # Left heart catheterization with coronary angiography and ventriculography
        "col2": "93452",  # Left heart catheterization only
        "description": "Left heart catheterization is a baseline component of combined coronary angiography.",
        "modifier_indicator": 0,
        "policy_rationale": "Comprehensive procedure code encompasses base catheterization.",
    },
    {
        "col1": "11104",  # Punch biopsy of skin, single lesion
        "col2": "11102",  # Tangential biopsy of skin
        "description": "Skin punch biopsy cannot be unbundled with tangential shave biopsy of the same anatomical site.",
        "modifier_indicator": 1,
        "policy_rationale": "Separate distinct anatomical lesions required for Modifier 59 / XS.",
    },
]

# MS-DRG Base Relative Weights and Base Payment Rate Benchmark (CMS FY2024 standardized base ~$6,500)
BASE_DRG_PAYMENT_RATE = 6500.0

MS_DRG_WEIGHTS: Dict[str, Dict[str, Any]] = {
    # Heart Failure
    "291": {"title": "Heart Failure and Shock with MCC", "relative_weight": 1.3412, "mcc_required": True, "cc_required": False},
    "292": {"title": "Heart Failure and Shock with CC", "relative_weight": 0.8924, "mcc_required": False, "cc_required": True},
    "293": {"title": "Heart Failure and Shock without CC/MCC", "relative_weight": 0.6128, "mcc_required": False, "cc_required": False},
    # Sepsis
    "870": {"title": "Septicemia or Severe Sepsis with MV >96 Hours", "relative_weight": 5.4210, "mcc_required": True, "cc_required": False},
    "871": {"title": "Septicemia or Severe Sepsis without MV >96 Hours with MCC", "relative_weight": 1.7825, "mcc_required": True, "cc_required": False},
    "872": {"title": "Septicemia or Severe Sepsis without MV >96 Hours without MCC", "relative_weight": 1.0842, "mcc_required": False, "cc_required": False},
    # Respiratory / Pneumonia
    "193": {"title": "Simple Pneumonia and Pleurisy with MCC", "relative_weight": 1.2580, "mcc_required": True, "cc_required": False},
    "194": {"title": "Simple Pneumonia and Pleurisy with CC", "relative_weight": 0.8415, "mcc_required": False, "cc_required": True},
    "195": {"title": "Simple Pneumonia and Pleurisy without CC/MCC", "relative_weight": 0.5890, "mcc_required": False, "cc_required": False},
}

# Major Complication/Comorbidity (MCC) and Complication/Comorbidity (CC) ICD-10 Dictionary
MCC_ICD10_CODES: Dict[str, str] = {
    "J96.01": "Acute respiratory failure with hypoxia (MCC)",
    "J96.00": "Acute respiratory failure, unspecified (MCC)",
    "I21.0": "Acute transmural myocardial infarction of anterior wall (MCC)",
    "N17.0": "Acute kidney failure with tubular necrosis (MCC)",
    "A41.9": "Sepsis, unspecified organism (MCC)",
    "R65.21": "Severe sepsis with septic shock (MCC)",
    "I46.9": "Cardiac arrest, cause unspecified (MCC)",
    "I50.21": "Acute systolic (congestive) heart failure (MCC)",
    "I50.31": "Acute diastolic (congestive) heart failure (MCC)",
}

CC_ICD10_CODES: Dict[str, str] = {
    "N17.9": "Acute kidney failure, unspecified (CC)",
    "E11.65": "Type 2 diabetes mellitus with hyperglycemia (CC)",
    "I50.9": "Heart failure, unspecified (CC)",
    "J44.1": "Chronic obstructive pulmonary disease with (acute) exacerbation (CC)",
    "E87.2": "Acidosis (CC)",
    "D62": "Acute posthemorrhagic anemia (CC)",
}


class MedicalCodingAuditorAgent:
    """Audits clinical coding accuracy to prevent compliance violations, unbundling, and revenue loss."""

    def __init__(self) -> None:
        self.agent_name = "MedicalCoding_RevenueIntegrityAgent"

    def audit_ncci_unbundling(
        self,
        assigned_cpt_codes: List[str],
        applied_modifiers: Optional[Dict[str, List[str]]] = None,
        clinical_note_text: str = "",
    ) -> List[Dict[str, Any]]:
        """Evaluates assigned CPT codes against NCCI Column 1 / Column 2 PTP unbundling edits."""
        findings: List[Dict[str, Any]] = []
        cpt_set = set(str(c).strip() for c in assigned_cpt_codes)
        applied_modifiers = applied_modifiers or {}
        text_lower = clinical_note_text.lower()

        for edit in NCCI_PTP_EDITS:
            col1 = edit["col1"]
            col2 = edit["col2"]

            if col1 in cpt_set and col2 in cpt_set:
                # Check if unbundling modifier is attached to Column 2
                col2_mods = applied_modifiers.get(col2, [])
                unbundling_modifiers = {"59", "XE", "XP", "XS", "XU"}
                has_unbundling_mod = bool(set(col2_mods).intersection(unbundling_modifiers))

                mod_indicator = edit["modifier_indicator"]

                if mod_indicator == 0:
                    # Indicator 0: Never allowed to unbundle
                    findings.append({
                        "issue_type": "NCCI_UNBUNDLING_MUTUALLY_EXCLUSIVE",
                        "severity": "CRITICAL",
                        "column1_code": col1,
                        "column2_code": col2,
                        "modifier_indicator": 0,
                        "description": (
                            f"NCCI PTP Edit Violation: CPT {col2} is inherently bundled into CPT {col1}. "
                            f"Modifier indicator is '0' (never unbundled). {edit['description']}"
                        ),
                        "recommendation": f"Remove CPT {col2} from claim submission to prevent formal denial.",
                    })
                elif mod_indicator == 1:
                    # Indicator 1: Allowed only if distinct anatomical site or separate patient encounter
                    if not has_unbundling_mod:
                        findings.append({
                            "issue_type": "NCCI_UNBUNDLING_MISSING_MODIFIER",
                            "severity": "HIGH",
                            "column1_code": col1,
                            "column2_code": col2,
                            "modifier_indicator": 1,
                            "description": (
                                f"NCCI PTP Edit: CPT {col2} is bundled into CPT {col1} without an appropriate "
                                f"anatomical / distinct procedural modifier (Modifier 59, XE, XP, XS, XU). {edit['description']}"
                            ),
                            "recommendation": (
                                f"Audit clinical documentation for separate anatomical sites or separate sessions. "
                                f"If substantiated, append Modifier 59 / XS to CPT {col2}; otherwise, remove CPT {col2}."
                            ),
                        })
                    else:
                        # Modifier is present: verify documentation actually justifies distinct site
                        distinct_keywords = ["separate lesion", "different site", "contralateral", "distinct polyp", "separate incision"]
                        justified = any(kw in text_lower for kw in distinct_keywords)
                        if not justified:
                            findings.append({
                                "issue_type": "UNSUPPORTED_MODIFIER_59",
                                "severity": "HIGH",
                                "column1_code": col1,
                                "column2_code": col2,
                                "modifier_used": list(set(col2_mods).intersection(unbundling_modifiers)),
                                "description": (
                                    f"Modifier 59 / X{{EPSU}} billed on CPT {col2}, but clinical narrative lacks "
                                    f"explicit documentation of separate anatomical sites or distinct surgical encounters."
                                ),
                                "recommendation": "Document exact anatomical separation or remove modifier and component code to avoid audit audit recoupment.",
                            })

        return findings

    def score_2023_ama_mdm(
        self,
        clinical_note_text: str,
        problem_count: int = 1,
        has_chronic_with_exacerbation: bool = False,
        has_threat_to_life: bool = False,
        data_reviewed_count: int = 0,
        independent_historian_used: bool = False,
        prescription_drug_managed: bool = False,
        high_risk_drug_monitoring: bool = False,
        emergency_surgery_decision: bool = False,
    ) -> Dict[str, Any]:
        """Calculates 2023 AMA Medical Decision Making (MDM) E/M complexity level."""
        text_lower = clinical_note_text.lower()

        # 1. Problems Element
        if has_threat_to_life or any(kw in text_lower for kw in ["unstable", "threat to life", "impending organ failure", "resuscitation", "intubated", "cardiogenic shock", "status epilepticus"]):
            problems_level = "HIGH"
            prob_score = 4
        elif has_chronic_with_exacerbation or any(kw in text_lower for kw in ["exacerbation", "decompensation", "severe progression", "uncontrolled"]) or problem_count >= 3:
            problems_level = "MODERATE"
            prob_score = 3
        elif problem_count >= 2 or any(kw in text_lower for kw in ["chronic stable", "acute uncomplicated"]):
            problems_level = "LOW"
            prob_score = 2
        else:
            problems_level = "MINIMAL"
            prob_score = 1

        # 2. Data Element
        data_points = data_reviewed_count
        if independent_historian_used or "historian" in text_lower or "family member provided history" in text_lower:
            data_points += 2
        if any(kw in text_lower for kw in ["independent interpretation", "reviewed images", "reviewed ct", "reviewed mri"]):
            data_points += 3
        if any(kw in text_lower for kw in ["discussed with specialist", "consulted cardiology", "consulted surgery"]):
            data_points += 2

        if data_points >= 4:
            data_level = "EXTENSIVE"
            data_score = 4
        elif data_points >= 3:
            data_level = "MODERATE"
            data_score = 3
        elif data_points >= 1:
            data_level = "LIMITED"
            data_score = 2
        else:
            data_level = "MINIMAL"
            data_score = 1

        # 3. Risk Element
        if emergency_surgery_decision or high_risk_drug_monitoring or any(kw in text_lower for kw in ["toxic monitoring", "warfarin titration", "chemotherapy decision", "emergency surgery", "intensive care transfer"]):
            risk_level = "HIGH"
            risk_score = 4
        elif prescription_drug_managed or any(kw in text_lower for kw in ["prescribed", "started on", "titrated medication", "iv fluids", "minor surgery"]):
            risk_level = "MODERATE"
            risk_score = 3
        elif any(kw in text_lower for kw in ["otc", "dressings", "gargles"]):
            risk_level = "LOW"
            risk_score = 2
        else:
            risk_level = "MINIMAL"
            risk_score = 1

        # AMA MDM 2-out-of-3 Rule: Sort the 3 element scores and take the second highest (median)
        element_scores = sorted([prob_score, data_score, risk_score])
        final_level_score = element_scores[1]  # 2nd highest

        level_map = {
            1: {"level": "Straightforward", "established_code": "99212", "new_patient_code": "99202"},
            2: {"level": "Low Complexity", "established_code": "99213", "new_patient_code": "99203"},
            3: {"level": "Moderate Complexity", "established_code": "99214", "new_patient_code": "99204"},
            4: {"level": "High Complexity", "established_code": "99215", "new_patient_code": "99205"},
        }
        computed_mdm = level_map[final_level_score]

        return {
            "problems_addressed": {"level": problems_level, "score": prob_score},
            "data_analyzed": {"level": data_level, "score": data_score, "data_points": data_points},
            "risk_of_management": {"level": risk_level, "score": risk_score},
            "mdm_overall_level": computed_mdm["level"],
            "recommended_established_cpt": computed_mdm["established_code"],
            "recommended_new_patient_cpt": computed_mdm["new_patient_code"],
        }

    def evaluate_drg_reimbursement(
        self,
        principal_diagnosis_icd10: str,
        secondary_diagnoses_icd10: List[str],
    ) -> Dict[str, Any]:
        """Calculates MS-DRG relative weight, MCC/CC presence, and estimated reimbursement impact."""
        sec_set = set(d.strip().upper() for d in secondary_diagnoses_icd10)
        p_clean = principal_diagnosis_icd10.strip().upper()

        # Identify MCCs and CCs
        mccs_found = [MCC_ICD10_CODES[code] for code in sec_set if code in MCC_ICD10_CODES]
        ccs_found = [CC_ICD10_CODES[code] for code in sec_set if code in CC_ICD10_CODES]

        has_mcc = len(mccs_found) > 0
        has_cc = len(ccs_found) > 0 and not has_mcc

        assigned_drg = "293"  # default fallback
        drg_title = "Heart Failure and Shock without CC/MCC"
        drg_weight = 0.6128

        # Sepsis family
        if p_clean.startswith("A41") or p_clean.startswith("R65"):
            if has_mcc:
                assigned_drg = "871"
                drg_title = MS_DRG_WEIGHTS["871"]["title"]
                drg_weight = MS_DRG_WEIGHTS["871"]["relative_weight"]
            else:
                assigned_drg = "872"
                drg_title = MS_DRG_WEIGHTS["872"]["title"]
                drg_weight = MS_DRG_WEIGHTS["872"]["relative_weight"]

        # Heart Failure family
        elif p_clean.startswith("I50"):
            if has_mcc:
                assigned_drg = "291"
                drg_title = MS_DRG_WEIGHTS["291"]["title"]
                drg_weight = MS_DRG_WEIGHTS["291"]["relative_weight"]
            elif has_cc:
                assigned_drg = "292"
                drg_title = MS_DRG_WEIGHTS["292"]["title"]
                drg_weight = MS_DRG_WEIGHTS["292"]["relative_weight"]
            else:
                assigned_drg = "293"
                drg_title = MS_DRG_WEIGHTS["293"]["title"]
                drg_weight = MS_DRG_WEIGHTS["293"]["relative_weight"]

        # Pneumonia family
        elif p_clean.startswith("J18") or p_clean.startswith("J15"):
            if has_mcc:
                assigned_drg = "193"
                drg_title = MS_DRG_WEIGHTS["193"]["title"]
                drg_weight = MS_DRG_WEIGHTS["193"]["relative_weight"]
            elif has_cc:
                assigned_drg = "194"
                drg_title = MS_DRG_WEIGHTS["194"]["title"]
                drg_weight = MS_DRG_WEIGHTS["194"]["relative_weight"]
            else:
                assigned_drg = "195"
                drg_title = MS_DRG_WEIGHTS["195"]["title"]
                drg_weight = MS_DRG_WEIGHTS["195"]["relative_weight"]

        est_reimbursement = round(drg_weight * BASE_DRG_PAYMENT_RATE, 2)

        return {
            "principal_diagnosis": principal_diagnosis_icd10,
            "assigned_ms_drg": assigned_drg,
            "drg_title": drg_title,
            "relative_weight": drg_weight,
            "has_mcc": has_mcc,
            "mccs_documented": mccs_found,
            "has_cc": has_cc,
            "ccs_documented": ccs_found,
            "estimated_reimbursement_usd": est_reimbursement,
        }

    def audit_coding_accuracy(
        self,
        clinical_note_text: str,
        assigned_icd10_codes: List[str],
        assigned_cpt_codes: List[str],
        applied_modifiers: Optional[Dict[str, List[str]]] = None,
        patient_id: Optional[Union[int, str]] = None,
    ) -> Dict[str, Any]:
        """Comprehensive audit covering ICD-10 clinical documentation, NCCI unbundling, and 2023 AMA MDM."""
        text_lower = clinical_note_text.lower()
        findings: List[Dict[str, Any]] = []
        is_compliant = True

        # 1. Diabetes ICD-10 check (backward compatibility)
        if "diabetes" in text_lower or "diabetic" in text_lower:
            if not any(code.startswith("E11") or code.startswith("E10") for code in assigned_icd10_codes):
                is_compliant = False
                findings.append({
                    "issue_type": "MISSING_DIAGNOSIS_CODE",
                    "severity": "HIGH",
                    "description": "Clinical note mentions Diabetes, but no E10/E11 ICD-10 code was billed.",
                })

        # 2. Heart Failure ICD-10 check
        if "heart failure" in text_lower or "chf" in text_lower or "reduced ejection fraction" in text_lower:
            if not any(code.startswith("I50") for code in assigned_icd10_codes):
                is_compliant = False
                findings.append({
                    "issue_type": "MISSING_DIAGNOSIS_CODE",
                    "severity": "HIGH",
                    "description": "Clinical note documents Heart Failure, but no I50 ICD-10 code was assigned.",
                })

        # 3. Acute Kidney Injury (AKI) check
        if "acute kidney injury" in text_lower or "aki" in text_lower or "creatinine spike" in text_lower:
            if not any(code.startswith("N17") for code in assigned_icd10_codes):
                is_compliant = False
                findings.append({
                    "issue_type": "MISSING_MCC_CC_DIAGNOSIS",
                    "severity": "MEDIUM",
                    "description": "Clinical note documents Acute Kidney Injury, but no N17 (MCC/CC) was billed.",
                })

        # 4. NCCI Unbundling & Modifier 59 Audit
        ncci_findings = self.audit_ncci_unbundling(
            assigned_cpt_codes=assigned_cpt_codes,
            applied_modifiers=applied_modifiers,
            clinical_note_text=clinical_note_text,
        )
        if ncci_findings:
            is_compliant = False
            findings.extend(ncci_findings)

        # 5. 2023 AMA MDM E/M Complexity Audit
        mdm_evaluation = self.score_2023_ama_mdm(clinical_note_text=clinical_note_text)
        recommended_cpt = mdm_evaluation["recommended_established_cpt"]

        # Check for Upcoding (e.g. 99215 billed when MDM supports <= 99214)
        if "99215" in assigned_cpt_codes:
            high_complexity_keywords = ["comorbidity", "multi-system", "resuscitation", "intensive", "threat to life"]
            has_high_complexity_narrative = any(kw in text_lower for kw in high_complexity_keywords)
            if not has_high_complexity_narrative and recommended_cpt != "99215":
                is_compliant = False
                findings.append({
                    "issue_type": "POTENTIAL_UPCODING",
                    "severity": "MEDIUM",
                    "description": (
                        f"CPT 99215 (High Complexity E&M) billed, but clinical note lacks high-complexity documentation "
                        f"(AMA MDM scored as {mdm_evaluation['mdm_overall_level']}, supporting {recommended_cpt})."
                    ),
                })

        # Check for Undercoding (e.g. 99213 billed when high MDM was documented)
        if "99213" in assigned_cpt_codes and recommended_cpt in ["99214", "99215"]:
            findings.append({
                "issue_type": "POTENTIAL_UNDERCODING",
                "severity": "LOW",
                "description": (
                    f"CPT 99213 billed, but documentation substantiates {mdm_evaluation['mdm_overall_level']} "
                    f"(supporting CPT {recommended_cpt}), causing potential revenue loss."
                ),
            })

        # 6. MS-DRG calculation if primary diagnosis available
        drg_info = None
        if assigned_icd10_codes:
            drg_info = self.evaluate_drg_reimbursement(
                principal_diagnosis_icd10=assigned_icd10_codes[0],
                secondary_diagnoses_icd10=assigned_icd10_codes[1:],
            )

        # 7. Formulate FHIR Action Proposals
        proposed_actions: List[Any] = []
        pid_str = str(patient_id) if patient_id is not None else "patient-audit"

        for f in findings:
            if f.get("severity") in ["CRITICAL", "HIGH"]:
                flag = FHIRFlagProposal(
                    patient_id=pid_str,
                    status="active",
                    category="clinical_alert",
                    severity="critical" if f.get("severity") == "CRITICAL" else "warning",
                    code="CODING_COMPLIANCE_ANOMALY",
                    details=f"{f['issue_type']}: {f['description']}",
                )
                proposed_actions.append(flag)

        clinical_response = ClinicalAgentResponse(
            recommendations=[
                {"compliance_status": "PASSED" if is_compliant else "AUDIT_FLAGGED"},
                {"total_findings": len(findings), "findings": findings},
                {"mdm_scoring": mdm_evaluation},
            ],
            proposed_fhir_actions=proposed_actions,
            epistemic_confidence=0.98 if is_compliant else 0.90,
            agent_name=self.agent_name,
            reasoning=f"Audited {len(assigned_icd10_codes)} ICD-10 and {len(assigned_cpt_codes)} CPT codes against NCCI and 2023 AMA MDM. Found {len(findings)} anomalies.",
            metadata={
                "assigned_icd10": assigned_icd10_codes,
                "assigned_cpt": assigned_cpt_codes,
                "mdm_level": mdm_evaluation["mdm_overall_level"],
                "drg_info": drg_info,
            },
        )

        return {
            "is_compliant": is_compliant,
            "total_findings": len(findings),
            "findings": findings,
            "audit_status": "PASSED" if is_compliant else "AUDIT_FLAGGED",
            "mdm_evaluation": mdm_evaluation,
            "drg_impact": drg_info,
            "proposed_fhir_actions": [a.to_dict() for a in proposed_actions],
            "clinical_response": clinical_response.to_dict(),
        }


# Singleton auditor agent instance
coding_auditor_agent = MedicalCodingAuditorAgent()
medical_coding_auditor = coding_auditor_agent

