"""Precision Oncology & Molecular Tumor Board (MDT) Case Reasoning Agent
======================================================================
Synthesizes oncology staging (TNM), pathology reports, somatic tumor genomic
alterations (EGFR, KRAS, BRAF, HER2, BRCA1/2, PD-L1, ALK, ROS1, RET, NTRK),
NCCN clinical evidence tiers (Category 1, Category 2A), targeted therapy
protocols, and pathway resistance dynamics into structured tumor board decisions.

Emits strongly-typed FHIR R4 action proposals (MedicationRequest, ServiceRequest, Flag)
and ClinicalAgentResponse.
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
        FHIRMedicationRequestProposal,
        FHIRServiceRequestProposal,
    )
except ImportError:
    @dataclass
    class FHIRMedicationRequestProposal:
        patient_id: str
        medication_name: str
        dosage: str
        route: str = "oral"
        frequency: str = "once daily"
        indication: str = ""
        clinical_evidence: Optional[List[str]] = None
        requester: Optional[str] = None
        intent: str = "order"
        priority: str = "routine"
        id: Optional[str] = None
        created_at: Optional[datetime.datetime] = None

        def __post_init__(self) -> None:
            if self.id is None:
                self.id = f"medreq-{uuid.uuid4().hex[:10]}"
            if self.created_at is None:
                self.created_at = datetime.datetime.now(datetime.timezone.utc)
            if self.clinical_evidence is None:
                self.clinical_evidence = []

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.created_at:
                data["created_at"] = self.created_at.isoformat()
            return data

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


# NCCN Evidence Guidelines and Targetable Therapies Knowledge Base
TARGETED_THERAPY_GUIDELINES: Dict[str, List[Dict[str, Any]]] = {
    "EGFR": [
        {
            "mutation_pattern": r"(l858r|exon\s*19\s*del|del19|e746_a750del)",
            "therapy": "Osimertinib",
            "dosage": "80 mg",
            "route": "oral",
            "frequency": "once daily",
            "nccn_category": "Category 1",
            "setting": "First-line preferred in metastatic EGFR-mutated NSCLC",
            "cancers": ["nsclc", "lung"],
            "rationale": "Third-generation CNS-penetrant EGFR TKI demonstrating superior PFS and OS vs first-generation TKIs (FLAURA trial).",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(t790m)",
            "therapy": "Osimertinib",
            "dosage": "80 mg",
            "route": "oral",
            "frequency": "once daily",
            "nccn_category": "Category 1",
            "setting": "Second-line after progression on 1st/2nd generation EGFR TKI (Gefitinib/Erlotinib/Afatinib)",
            "cancers": ["nsclc", "lung"],
            "rationale": "Potent activity against acquired T790M gatekeeper resistance mutation (AURA3 trial).",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(exon\s*20\s*ins|insertion)",
            "therapy": "Amivantamab-vmjw",
            "dosage": "1050 mg (weight <80kg) or 1400 mg (weight >=80kg)",
            "route": "intravenous",
            "frequency": "weekly for 4 weeks then Q2W",
            "nccn_category": "Category 2A",
            "setting": "Subsequent therapy after platinum progression for EGFR exon 20 insertions",
            "cancers": ["nsclc", "lung"],
            "rationale": "Bispecific EGFR-MET antibody with antibody-dependent cellular cytotoxicity targeting exon 20 insertions.",
            "contraindicated_in": [],
        },
    ],
    "KRAS": [
        {
            "mutation_pattern": r"(g12c)",
            "therapy": "Sotorasib",
            "dosage": "960 mg",
            "route": "oral",
            "frequency": "once daily",
            "nccn_category": "Category 2A",
            "setting": "Second-line or subsequent therapy in locally advanced or metastatic NSCLC with KRAS G12C mutation",
            "cancers": ["nsclc", "lung"],
            "rationale": "First-in-class covalent KRAS G12C inhibitor binding the switch II pocket to lock KRAS in inactive GDP state.",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(g12c)",
            "therapy": "Adagrasib",
            "dosage": "600 mg",
            "route": "oral",
            "frequency": "twice daily",
            "nccn_category": "Category 2A",
            "setting": "Second-line therapy in metastatic NSCLC or combined with Cetuximab in metastatic Colorectal Cancer",
            "cancers": ["nsclc", "lung", "colorectal", "colon"],
            "rationale": "Irreversible KRAS G12C inhibitor with CNS penetration; synergistic with EGFR blockade in CRC.",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(g12d|g12v|g13d|q61)",
            "therapy": "Clinical Trial / Pan-KRAS Investigational Inhibitor",
            "dosage": "Per Protocol",
            "route": "oral",
            "frequency": "per protocol",
            "nccn_category": "Category 2A",
            "setting": "Basket trial for non-G12C KRAS mutations",
            "cancers": ["pancreatic", "colorectal", "colon", "nsclc", "lung"],
            "rationale": "Non-G12C KRAS mutations confer constitutive downstream MAPK activation without G12C-specific pocket.",
            "contraindicated_in": ["panitumumab", "cetuximab"],
        },
    ],
    "BRAF": [
        {
            "mutation_pattern": r"(v600e|v600k)",
            "therapy": "Dabrafenib + Trametinib",
            "dosage": "Dabrafenib 150 mg BID + Trametinib 2 mg daily",
            "route": "oral",
            "frequency": "BID / once daily",
            "nccn_category": "Category 1",
            "setting": "First-line or subsequent in BRAF V600E mutant metastatic Melanoma, NSCLC, or Anaplastic Thyroid Cancer",
            "cancers": ["melanoma", "nsclc", "lung", "thyroid", "anaplastic"],
            "rationale": "Dual vertical MAPK pathway inhibition (BRAF kinase inhibitor + MEK1/2 inhibitor) suppressing paradoxical ERK reactivation.",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(v600e)",
            "therapy": "Encorafenib + Cetuximab",
            "dosage": "Encorafenib 300 mg daily + Cetuximab 400 mg/m2 load then 250 mg/m2 weekly",
            "route": "oral / intravenous",
            "frequency": "daily / weekly",
            "nccn_category": "Category 1",
            "setting": "Second-line or subsequent in BRAF V600E mutant metastatic Colorectal Cancer",
            "cancers": ["colorectal", "colon", "rectal"],
            "rationale": "Overcomes rapid EGFR feedback reactivation seen with single-agent BRAF inhibition in colorectal cancer (BEACON CRC trial).",
            "contraindicated_in": [],
        },
    ],
    "HER2": [
        {
            "mutation_pattern": r"(amplified|3\+|ihc\s*3|overexpression|erbb2\s*amp)",
            "therapy": "Trastuzumab Deruxtecan (T-DXd)",
            "dosage": "5.4 mg/kg",
            "route": "intravenous",
            "frequency": "every 3 weeks",
            "nccn_category": "Category 1",
            "setting": "Second-line or subsequent in HER2-positive or HER2-low metastatic Breast Cancer and HER2-mutant NSCLC",
            "cancers": ["breast", "gastric", "nsclc", "lung"],
            "rationale": "HER2-directed antibody-drug conjugate with cleavable tetrapeptide-based linker and topoisomerase I inhibitor payload (DESTINY trials).",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(amplified|3\+|ihc\s*3)",
            "therapy": "Trastuzumab + Pertuzumab + Docetaxel",
            "dosage": "Trastuzumab 8 mg/kg load -> 6 mg/kg, Pertuzumab 840 mg load -> 420 mg, Docetaxel 75 mg/m2",
            "route": "intravenous",
            "frequency": "every 3 weeks",
            "nccn_category": "Category 1",
            "setting": "First-line preferred regimen for HER2-positive metastatic Breast Cancer",
            "cancers": ["breast"],
            "rationale": "Dual HER2 dimerization domain II and IV blockade providing synergistic antiproliferative and apoptotic activity (CLEOPATRA trial).",
            "contraindicated_in": [],
        },
    ],
    "BRCA1": [
        {
            "mutation_pattern": r"(pathogenic|deleterious|mutated|mutation|loss\s*of\s*function)",
            "therapy": "Olaparib",
            "dosage": "300 mg",
            "route": "oral",
            "frequency": "twice daily",
            "nccn_category": "Category 1",
            "setting": "Maintenance/subsequent therapy for BRCA1/2-mutated Ovarian, HER2- Breast, Pancreatic, or mCRPC",
            "cancers": ["ovarian", "breast", "pancreatic", "prostate"],
            "rationale": "PARP1/2 inhibitor inducing synthetic lethality in homologous recombination repair deficient (HRD) tumors.",
            "contraindicated_in": [],
        }
    ],
    "BRCA2": [
        {
            "mutation_pattern": r"(pathogenic|deleterious|mutated|mutation|loss\s*of\s*function)",
            "therapy": "Olaparib",
            "dosage": "300 mg",
            "route": "oral",
            "frequency": "twice daily",
            "nccn_category": "Category 1",
            "setting": "Maintenance/subsequent therapy for BRCA1/2-mutated Ovarian, HER2- Breast, Pancreatic, or mCRPC",
            "cancers": ["ovarian", "breast", "pancreatic", "prostate"],
            "rationale": "PARP1/2 inhibitor inducing synthetic lethality in homologous recombination repair deficient (HRD) tumors.",
            "contraindicated_in": [],
        }
    ],
    "PD-L1": [
        {
            "mutation_pattern": r"(tps\s*>=?\s*50%?|high\s*express|>=?\s*50%)",
            "therapy": "Pembrolizumab",
            "dosage": "200 mg Q3W or 400 mg Q6W",
            "route": "intravenous",
            "frequency": "every 3 or 6 weeks",
            "nccn_category": "Category 1",
            "setting": "First-line monotherapy in metastatic NSCLC with PD-L1 TPS >= 50% and EGFR/ALK negative",
            "cancers": ["nsclc", "lung"],
            "rationale": "Immune checkpoint inhibitor blocking PD-1/PD-L1 axis to reinvigorate exhausted tumor-infiltrating cytotoxic T lymphocytes (KEYNOTE-024 trial).",
            "contraindicated_in": [],
        },
        {
            "mutation_pattern": r"(tps\s*1-49%?|1-49%|positive)",
            "therapy": "Pembrolizumab + Platinum-Pemetrexed",
            "dosage": "Pembrolizumab 200 mg + Carboplatin AUC 5 + Pemetrexed 500 mg/m2",
            "route": "intravenous",
            "frequency": "every 3 weeks",
            "nccn_category": "Category 1",
            "setting": "First-line chemo-immunotherapy in metastatic non-squamous NSCLC with PD-L1 TPS 1-49%",
            "cancers": ["nsclc", "lung"],
            "rationale": "Chemo-immunotherapy combination yielding superior OS over chemotherapy alone across all PD-L1 strata (KEYNOTE-189 trial).",
            "contraindicated_in": [],
        },
    ],
    "ALK": [
        {
            "mutation_pattern": r"(positive|rearrangement|fusion|eml4-alk)",
            "therapy": "Alectinib",
            "dosage": "600 mg",
            "route": "oral",
            "frequency": "twice daily with food",
            "nccn_category": "Category 1",
            "setting": "First-line preferred in metastatic ALK-positive NSCLC",
            "cancers": ["nsclc", "lung"],
            "rationale": "Second-generation highly selective ALK inhibitor with exceptional CNS activity and prolonged PFS (ALEX trial).",
            "contraindicated_in": [],
        }
    ],
}


class TumorBoardAgent:
    """Precision Oncology & Molecular Tumor Board Clinical Reasoning Agent."""

    def __init__(self) -> None:
        self.agent_name = "PrecisionOncology_TumorBoardAgent"

    def match_guideline_therapies(
        self,
        cancer_type: str,
        genomic_biomarkers: Dict[str, str],
        prior_therapies: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Matches patient biomarkers and cancer type against NCCN evidence guidelines."""
        matched: List[Dict[str, Any]] = []
        prior_str = " ".join(prior_therapies or []).lower()
        cancer_clean = cancer_type.lower()

        for gene, result in genomic_biomarkers.items():
            gene_upper = gene.upper().strip()
            result_clean = str(result).lower().strip()

            guidelines = TARGETED_THERAPY_GUIDELINES.get(gene_upper, [])
            for g in guidelines:
                # Check mutation pattern match
                if not re.search(g["mutation_pattern"], result_clean):
                    continue

                # Check cancer type applicability
                cancer_match = any(c in cancer_clean for c in g["cancers"]) if g["cancers"] else True
                if not cancer_match:
                    continue

                # Check if therapy was already tried and progressed on
                already_tried = any(g["therapy"].lower() in prior_str for _ in [1])

                matched.append({
                    "gene": gene_upper,
                    "biomarker_status": result,
                    "therapy": g["therapy"],
                    "dosage": g["dosage"],
                    "route": g["route"],
                    "frequency": g["frequency"],
                    "nccn_category": g["nccn_category"],
                    "setting": g["setting"],
                    "rationale": g["rationale"],
                    "already_exhausted": already_tried,
                    "contraindicated_drugs": g.get("contraindicated_in", []),
                })

        return matched

    def evaluate_pathway_resistance(
        self,
        cancer_type: str,
        genomic_biomarkers: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Detects biological pathway resistance and therapy contraindications."""
        resistance_findings: List[Dict[str, str]] = []
        cancer_lower = cancer_type.lower()
        biomarker_keys = {k.upper(): str(v).lower() for k, v in genomic_biomarkers.items()}

        # 1. KRAS mutation in Colorectal Cancer -> Resistance to anti-EGFR mAbs (Cetuximab, Panitumumab)
        if any(c in cancer_lower for c in ["colorectal", "colon", "rectal"]):
            kras_val = biomarker_keys.get("KRAS", "")
            if any(mut in kras_val for mut in ["mutat", "g12", "g13", "q61"]):
                resistance_findings.append({
                    "gene": "KRAS",
                    "status": kras_val,
                    "resistance_type": "PRIMARY_RESISTANCE",
                    "contraindicated_class": "Anti-EGFR Monoclonal Antibodies (Cetuximab, Panitumumab)",
                    "clinical_warning": (
                        "KRAS codon 12/13/61 activating mutation confers constitutive GTPase activation, "
                        "rendering upstream EGFR blockade ineffective. Anti-EGFR therapy is strictly contraindicated."
                    ),
                    "nccn_tier": "Category 1",
                })

        # 2. EGFR C797S resistance to Osimertinib
        egfr_val = biomarker_keys.get("EGFR", "")
        if "c797s" in egfr_val:
            resistance_findings.append({
                "gene": "EGFR",
                "status": egfr_val,
                "resistance_type": "SECONDARY_RESISTANCE",
                "contraindicated_class": "Third-Generation Covalent EGFR TKIs (Osimertinib monotherapy)",
                "clinical_warning": (
                    "EGFR C797S mutation disrupts the covalent cysteine-binding pocket for Osimertinib. "
                    "Recommend clinical trial or combined 1st/3rd-gen TKI if in trans with T790M."
                ),
                "nccn_tier": "Category 2A",
            })

        return resistance_findings

    def evaluate_case(
        self,
        patient_id: Union[int, str],
        patient_name: str,
        cancer_type: str,
        tnm_stage: str,
        pathology_summary: str,
        genomic_biomarkers: Dict[str, str],
        prior_therapies: Optional[List[str]] = None,
        ecog_ps: int = 1,
    ) -> ClinicalAgentResponse:
        """Deep clinical evaluation returning strongly-typed ClinicalAgentResponse with FHIR proposals."""
        prior_therapies = prior_therapies or []
        pid_str = str(patient_id)

        # 1. Match guideline therapies
        matched_therapies = self.match_guideline_therapies(
            cancer_type=cancer_type,
            genomic_biomarkers=genomic_biomarkers,
            prior_therapies=prior_therapies,
        )

        # 2. Identify pathway resistances
        resistances = self.evaluate_pathway_resistance(
            cancer_type=cancer_type,
            genomic_biomarkers=genomic_biomarkers,
        )

        # 3. Formulate FHIR Action Proposals
        proposed_actions: List[Any] = []
        recommendations: List[Union[str, Dict[str, Any]]] = []

        # Medication proposals for active matched therapies
        for t in matched_therapies:
            if not t["already_exhausted"]:
                med_prop = FHIRMedicationRequestProposal(
                    patient_id=pid_str,
                    medication_name=t["therapy"],
                    dosage=t["dosage"],
                    route=t["route"],
                    frequency=t["frequency"],
                    indication=f"{cancer_type} with {t['gene']} ({t['biomarker_status']})",
                    clinical_evidence=[
                        f"NCCN {t['nccn_category']}",
                        t["rationale"],
                    ],
                    priority="routine",
                )
                proposed_actions.append(med_prop)

                recommendations.append({
                    "action_type": "TARGETED_THERAPY",
                    "gene": t["gene"],
                    "biomarker": t["biomarker_status"],
                    "therapy": t["therapy"],
                    "nccn_evidence": t["nccn_category"],
                    "rationale": t["rationale"],
                })

        # ServiceRequest proposals for monitoring/reflex testing
        sr_monitoring = FHIRServiceRequestProposal(
            patient_id=pid_str,
            category="laboratory",
            code="69548-6",  # Genetic variant assessment
            description=f"Serial ctDNA liquid biopsy monitoring for {cancer_type} targeted therapy response",
            urgency="routine",
            indication=f"Genomic monitoring for {cancer_type} on targeted protocol",
            supporting_info=[f"Baseline biomarkers: {genomic_biomarkers}"],
        )
        proposed_actions.append(sr_monitoring)

        # Flag proposals for critical resistances or actionable driver alterations
        for r in resistances:
            flag_prop = FHIRFlagProposal(
                patient_id=pid_str,
                status="active",
                category="clinical_alert",
                severity="critical",
                code="RESISTANCE_FLAG",
                details=f"CONTRAINDICATION: {r['contraindicated_class']}. {r['clinical_warning']}",
            )
            proposed_actions.append(flag_prop)
            recommendations.append({
                "action_type": "CONTRAINDICATION_ALERT",
                "gene": r["gene"],
                "resistance_type": r["resistance_type"],
                "warning": r["clinical_warning"],
            })

        # Compute epistemic confidence
        if matched_therapies:
            # Category 1 confers highest confidence
            has_cat1 = any(t["nccn_category"] == "Category 1" for t in matched_therapies)
            confidence = 0.95 if has_cat1 else 0.88
        else:
            confidence = 0.70

        reasoning = (
            f"Evaluated {cancer_type} (Stage {tnm_stage}) against NCCN Guidelines. "
            f"Identified {len(matched_therapies)} guideline-concordant therapy options and "
            f"{len(resistances)} pathway resistance alerts."
        )

        return ClinicalAgentResponse(
            recommendations=recommendations,
            proposed_fhir_actions=proposed_actions,
            epistemic_confidence=confidence,
            agent_name=self.agent_name,
            reasoning=reasoning,
            metadata={
                "patient_name": patient_name,
                "cancer_type": cancer_type,
                "tnm_stage": tnm_stage,
                "pathology_summary": pathology_summary,
                "genomic_biomarkers": genomic_biomarkers,
                "ecog_ps": ecog_ps,
            },
        )

    def generate_tumor_board_summary(
        self,
        patient_id: int,
        patient_name: str,
        cancer_type: str,
        tnm_stage: str,
        pathology_summary: str,
        genomic_biomarkers: Dict[str, str],
        prior_therapies: List[str],
        ecog_ps: int = 1,
    ) -> Dict[str, Any]:
        """Backward-compatible method returning legacy summary dict enriched with deep reasoning."""
        clinical_response = self.evaluate_case(
            patient_id=patient_id,
            patient_name=patient_name,
            cancer_type=cancer_type,
            tnm_stage=tnm_stage,
            pathology_summary=pathology_summary,
            genomic_biomarkers=genomic_biomarkers,
            prior_therapies=prior_therapies,
            ecog_ps=ecog_ps,
        )

        biomarker_str = ", ".join(f"{k}: {v}" for k, v in genomic_biomarkers.items()) or "None detected"

        matched = self.match_guideline_therapies(cancer_type, genomic_biomarkers, prior_therapies)
        resistances = self.evaluate_pathway_resistance(cancer_type, genomic_biomarkers)

        therapy_lines = []
        for m in matched:
            status_tag = " [EXHAUSTED]" if m["already_exhausted"] else " [RECOMMENDED]"
            therapy_lines.append(
                f"- {m['therapy']} ({m['dosage']} {m['route']} {m['frequency']}) — {m['nccn_category']}{status_tag}\n"
                f"  Rationale: {m['rationale']}"
            )
        therapy_text = "\n".join(therapy_lines) if therapy_lines else "None identified under Category 1/2A."

        resistance_lines = [f"- {r['contraindicated_class']}: {r['clinical_warning']}" for r in resistances]
        resistance_text = "\n".join(resistance_lines) if resistance_lines else "No pathway resistance detected."

        summary_card = (
            f"MULTI-DISCIPLINARY TUMOR BOARD BRIEFING\n"
            f"Patient: {patient_name} (ID #{patient_id})\n"
            f"Cancer Diagnosis: {cancer_type} (Stage: {tnm_stage}, ECOG PS: {ecog_ps})\n\n"
            f"PATHOLOGY SUMMARY:\n{pathology_summary}\n\n"
            f"GENOMIC BIOMARKERS:\n{biomarker_str}\n\n"
            f"GUIDELINE-CONCORDANT TARGETED THERAPIES:\n{therapy_text}\n\n"
            f"PATHWAY RESISTANCES & CONTRAINDICATIONS:\n{resistance_text}\n\n"
            f"PRIOR THERAPIES:\n- {', '.join(prior_therapies) or 'None'}\n"
        )

        has_actionable_target = any(
            any(kw in v.lower() for kw in ["mutat", "positiv", "amplif", "overexpress", "rearrange", "fusion"])
            for v in genomic_biomarkers.values()
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "cancer_type": cancer_type,
            "tnm_stage": tnm_stage,
            "summary_card": summary_card,
            "has_actionable_genomic_target": has_actionable_target,
            "board_review_status": "READY_FOR_MDT_PRESENTATION",
            "matched_targeted_therapies": matched,
            "pathway_resistances": resistances,
            "clinical_response": clinical_response.to_dict(),
            "proposed_fhir_actions": [a.to_dict() for a in clinical_response.proposed_fhir_actions],
        }


# Singleton agent instance
tumor_board_agent = TumorBoardAgent()

