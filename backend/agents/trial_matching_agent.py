"""Biomarker-Driven Clinical Trial Eligibility Matching Agent
============================================================
Screens complex oncology and systemic disease patient health profiles (diagnoses,
somatic genomic alterations, organ reserve, prior therapies, ECOG performance status)
against a curated registry of Basket, Umbrella, and Protocol-driven clinical trials.

Emits structured trial matching scores, inclusion/exclusion breakdowns,
FHIR ServiceRequest proposals, and ClinicalAgentResponse.
"""

from __future__ import annotations

import datetime
import os
import re
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


CURATED_TRIAL_REGISTRY: List[Dict[str, Any]] = [
    # Legacy cardiometabolic trials
    {
        "nct_id": "NCT04253123",
        "title": "Novel SGLT2 Inhibitor in Type 2 Diabetes & Chronic Kidney Disease",
        "trial_type": "PROTOCOL_SPECIFIC",
        "condition": "diabetes",
        "min_age": 18,
        "max_age": 75,
        "required_icd10": ["E11.9", "N18.3", "E11", "N18"],
        "min_egfr": 30.0,
        "max_egfr": 60.0,
        "phase": "Phase III",
        "target_biomarker": None,
        "ecog_max": 2,
    },
    {
        "nct_id": "NCT05124987",
        "title": "PCSK9 Monoclonal Antibody for Early Coronary Artery Disease",
        "trial_type": "PROTOCOL_SPECIFIC",
        "condition": "heart",
        "min_age": 40,
        "max_age": 80,
        "required_icd10": ["I10", "I25.10", "I25"],
        "phase": "Phase II",
        "target_biomarker": None,
        "ecog_max": 2,
    },
    # Oncology Basket Trials (Tissue-Agnostic / Molecular Alteration Driven)
    {
        "nct_id": "NCT03108885",
        "title": "Master Basket Trial of Targeted Therapies for Somatic BRAF V600E Alterations across Advanced Solid Tumors",
        "trial_type": "BASKET",
        "condition": "cancer",
        "min_age": 18,
        "max_age": 85,
        "required_icd10": ["C34", "C18", "C43", "C73", "C80"],
        "min_egfr": 30.0,
        "phase": "Phase II",
        "target_gene": "BRAF",
        "target_biomarker": r"(v600e|v600k)",
        "ecog_max": 2,
        "description": "Histology-agnostic basket protocol evaluating combined BRAF+MEK inhibition in non-melanoma solid tumors.",
    },
    {
        "nct_id": "NCT04625647",
        "title": "Pan-Tumor Basket Trial of Next-Gen HER2-Directed Antibody-Drug Conjugate in ERBB2-Altered Solid Malignancies",
        "trial_type": "BASKET",
        "condition": "cancer",
        "min_age": 18,
        "max_age": 85,
        "required_icd10": ["C50", "C34", "C16", "C18"],
        "min_egfr": 30.0,
        "phase": "Phase II",
        "target_gene": "HER2",
        "target_biomarker": r"(amplif|3\+|ihc\s*3|overexpression|erbb2|mutation)",
        "ecog_max": 2,
        "description": "Evaluates novel cleavable-linker HER2 ADC across metastatic breast, lung, gastric, and colorectal tumors.",
    },
    {
        "nct_id": "NCT04185883",
        "title": "CodeBreaK 101: Phase 1b/2 Basket Study of Sotorasib Combinations in Advanced KRAS G12C Solid Tumors",
        "trial_type": "BASKET",
        "condition": "cancer",
        "min_age": 18,
        "max_age": 85,
        "required_icd10": ["C34", "C18", "C25"],
        "min_egfr": 40.0,
        "phase": "Phase Ib/II",
        "target_gene": "KRAS",
        "target_biomarker": r"(g12c)",
        "ecog_max": 1,
        "description": "Multi-arm basket evaluating covalent KRAS G12C inhibitor monotherapy and immuno-oncology combinations.",
    },
    {
        "nct_id": "NCT03844932",
        "title": "Phase II Basket Study of Synthetic Lethality PARP Inhibitor Combinations in Homologous Recombination Repair Deficient Tumors",
        "trial_type": "BASKET",
        "condition": "cancer",
        "min_age": 18,
        "max_age": 85,
        "required_icd10": ["C56", "C50", "C25", "C61"],
        "min_egfr": 30.0,
        "phase": "Phase II",
        "target_gene": "BRCA1",
        "target_biomarker": r"(pathogenic|deleterious|mutat)",
        "ecog_max": 2,
        "description": "Explores PARP inhibition synergy with ATR and checkpoint inhibitors in BRCA1/2 and ATM deficient solid tumors.",
    },
    # Oncology Umbrella Trials (Disease-Specific, Sub-Study Molecular Stratification)
    {
        "nct_id": "NCT02154490",
        "title": "Lung-MAP (S1400): Precision Medicine Umbrella Master Protocol for Advanced Non-Small Cell Lung Cancer",
        "trial_type": "UMBRELLA",
        "condition": "nsclc",
        "min_age": 18,
        "max_age": 85,
        "required_icd10": ["C34", "C34.90", "C34.1"],
        "min_egfr": 35.0,
        "phase": "Phase II/III",
        "target_gene": "EGFR",
        "target_biomarker": r"(l858r|exon\s*19|t790m|exon\s*20|kras|braf)",
        "ecog_max": 2,
        "description": "National master umbrella protocol matching second-line squamous and non-squamous NSCLC to biomarker sub-studies.",
    },
    {
        "nct_id": "NCT03404856",
        "title": "COLOMATE: Colorectal Molecularly Assigned Therapy Umbrella Master Protocol",
        "trial_type": "UMBRELLA",
        "condition": "colorectal",
        "min_age": 18,
        "max_age": 80,
        "required_icd10": ["C18", "C19", "C20"],
        "min_egfr": 40.0,
        "phase": "Phase II",
        "target_gene": "KRAS",
        "target_biomarker": r"(g12c|braf|her2|msi)",
        "ecog_max": 1,
        "description": "Platform umbrella study screening refractory metastatic CRC for sub-arms including HER2 amplification, KRAS G12C, and BRAF V600E.",
    },
]


class ClinicalTrialMatchingAgent:
    """Matches patient records against clinical trials to identify recruitment candidates."""

    def __init__(self) -> None:
        self.agent_name = "ClinicalTrialMatchingAgent"

    def match_patient_to_trials(
        self,
        age: int,
        primary_condition: str,
        egfr: Optional[float] = None,
        icd10_codes: Optional[List[str]] = None,
        biomarkers: Optional[Dict[str, str]] = None,
        ecog_ps: int = 1,
        has_active_brain_metastases: bool = False,
    ) -> List[Dict[str, Any]]:
        """Evaluates patient clinical profile against the trial registry and returns scored candidates."""
        matches: List[Dict[str, Any]] = []
        cond_lower = primary_condition.lower()
        patient_icd10 = set(icd10_codes or [])
        biomarkers = biomarkers or {}

        for trial in CURATED_TRIAL_REGISTRY:
            score = 0
            reasons: List[str] = []
            exclusions: List[str] = []

            # 1. Age match
            if trial["min_age"] <= age <= trial["max_age"]:
                score += 25
                reasons.append(f"Age {age} meets inclusion range [{trial['min_age']}-{trial['max_age']}]")
            else:
                continue

            # 2. Condition match
            trial_cond = trial["condition"].lower()
            if trial_cond in cond_lower or any(trial_cond in icd.lower() for icd in patient_icd10) or (trial_cond == "cancer" and any(c in cond_lower for c in ["cancer", "carcinoma", "tumor", "nsclc", "melanoma", "colorectal", "breast", "ovarian"])):
                score += 25
                reasons.append(f"Condition '{primary_condition}' aligns with trial protocol target ({trial['condition']})")
            elif trial.get("trial_type") == "BASKET" and biomarkers:
                # Basket trials are histology-agnostic if biomarker matches
                score += 15
                reasons.append("Histology-agnostic basket protocol eligible via molecular alteration")
            else:
                continue

            # 3. Biomarker match (Core molecular criterion for Basket & Umbrella)
            target_gene = trial.get("target_gene")
            target_pattern = trial.get("target_biomarker")
            biomarker_matched = False

            if target_gene and target_pattern and biomarkers:
                for gene, status in biomarkers.items():
                    if gene.upper() == target_gene.upper() or (target_gene == "BRCA1" and gene.upper() in ["BRCA1", "BRCA2"]):
                        if re.search(target_pattern, str(status).lower()):
                            score += 35
                            biomarker_matched = True
                            reasons.append(
                                f"Key molecular target {gene} '{status}' satisfies protocol genomic eligibility"
                            )
                            break
            elif not target_gene:
                # Non-biomarker specific trial
                score += 10

            # 4. Renal function (eGFR)
            if "min_egfr" in trial and egfr is not None:
                if trial["min_egfr"] <= egfr <= trial.get("max_egfr", 120.0):
                    score += 20
                    reasons.append(f"eGFR {egfr} mL/min satisfies trial renal safety threshold (>= {trial['min_egfr']})")
                else:
                    exclusions.append(f"eGFR {egfr} outside acceptable protocol window [{trial['min_egfr']}-{trial.get('max_egfr', 120.0)}]")

            # 5. ICD-10 overlap
            required_icd = trial.get("required_icd10", [])
            if required_icd:
                overlap = [code for code in patient_icd10 if any(code.startswith(req) for req in required_icd)]
                if overlap:
                    score += 15
                    reasons.append(f"Diagnostic ICD-10 concordance confirmed ({', '.join(overlap)})")

            # 6. Performance status check
            max_ecog = trial.get("ecog_max", 2)
            if ecog_ps <= max_ecog:
                score += 10
                reasons.append(f"ECOG PS {ecog_ps} satisfies protocol functional threshold (<= {max_ecog})")
            else:
                exclusions.append(f"ECOG PS {ecog_ps} exceeds protocol eligibility threshold (<= {max_ecog})")

            # 7. Exclusion check: Active untreated CNS metastases
            if has_active_brain_metastases and trial.get("trial_type") in ["BASKET", "UMBRELLA"]:
                exclusions.append("Active untreated CNS metastases trigger exclusion criteria.")

            # If hard exclusions present, downgrade match
            if exclusions:
                score = max(0, score - 40)

            match_percentage = min(100, score)
            if match_percentage >= 50 and not exclusions:
                matches.append({
                    "nct_id": trial["nct_id"],
                    "title": trial["title"],
                    "trial_type": trial.get("trial_type", "PROTOCOL_SPECIFIC"),
                    "phase": trial["phase"],
                    "match_score": match_percentage,
                    "biomarker_matched": biomarker_matched,
                    "eligibility_reasons": reasons,
                    "exclusions_flagged": exclusions,
                    "status": "ELIGIBLE" if match_percentage >= 70 else "POTENTIAL",
                })

        return sorted(matches, key=lambda x: x["match_score"], reverse=True)

    def evaluate_case_proposals(
        self,
        patient_id: Union[int, str],
        patient_name: str,
        age: int,
        primary_condition: str,
        egfr: Optional[float] = None,
        icd10_codes: Optional[List[str]] = None,
        biomarkers: Optional[Dict[str, str]] = None,
        ecog_ps: int = 1,
    ) -> ClinicalAgentResponse:
        """Deep evaluation generating structured ClinicalAgentResponse with FHIR ServiceRequest proposals."""
        pid_str = str(patient_id)
        matches = self.match_patient_to_trials(
            age=age,
            primary_condition=primary_condition,
            egfr=egfr,
            icd10_codes=icd10_codes,
            biomarkers=biomarkers,
            ecog_ps=ecog_ps,
        )

        proposed_actions: List[Any] = []
        recommendations: List[Union[str, Dict[str, Any]]] = []

        eligible_trials = [m for m in matches if m["status"] == "ELIGIBLE"]

        for t in eligible_trials[:2]:  # Top 2 eligible trials
            sr_trial = FHIRServiceRequestProposal(
                patient_id=pid_str,
                category="consult",
                code="306206005",  # Referral to clinical trial
                description=f"Clinical Trial Screening & Consent Referral: {t['nct_id']} ({t['title'][:60]})",
                urgency="routine",
                indication=f"Patient matches {t['trial_type']} protocol criteria with score {t['match_score']}%",
                supporting_info=t["eligibility_reasons"],
            )
            proposed_actions.append(sr_trial)

            flag_trial = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="clinical_alert",
                severity="warning",
                code="TRIAL_CANDIDATE",
                details=f"Candidate for {t['phase']} {t['trial_type']} trial {t['nct_id']}. Match score: {t['match_score']}%.",
            )
            proposed_actions.append(flag_trial)

            recommendations.append({
                "action_type": "TRIAL_RECRUITMENT",
                "nct_id": t["nct_id"],
                "trial_type": t["trial_type"],
                "phase": t["phase"],
                "match_score": t["match_score"],
                "rationale": "; ".join(t["eligibility_reasons"]),
            })

        confidence = 0.92 if eligible_trials else 0.70

        return ClinicalAgentResponse(
            recommendations=recommendations,
            proposed_fhir_actions=proposed_actions,
            epistemic_confidence=confidence,
            agent_name=self.agent_name,
            reasoning=f"Screened patient against {len(CURATED_TRIAL_REGISTRY)} clinical trial protocols. Found {len(eligible_trials)} eligible trial matches.",
            metadata={
                "patient_name": patient_name,
                "primary_condition": primary_condition,
                "total_matches": len(matches),
            },
        )


# Singleton agent instance
trial_matching_agent = ClinicalTrialMatchingAgent()

