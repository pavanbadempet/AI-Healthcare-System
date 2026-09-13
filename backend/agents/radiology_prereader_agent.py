"""Multi-Modal Radiology Automated Pre-Reader Agent
=================================================
Analyzes diagnostic imaging metadata, American College of Radiology (ACR)
Appropriateness Criteria (scores 1-9), Hounsfield Unit (HU) tissue attenuation
windowing and density profiling, structured RADS preliminary impressions, and
broadcasts STAT critical alerts for life-threatening emergency findings.

Emits strongly-typed FHIR action proposals and ClinicalAgentResponse.
"""

from __future__ import annotations

import datetime
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

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
    import uuid
    from dataclasses import asdict

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


# ── ACR APPROPRIATENESS CRITERIA KNOWLEDGE BASE ──────────────────────────────

ACR_APPROPRIATENESS_RULES: List[Dict[str, Any]] = [
    {
        "indication_keywords": ["thunderclap headache", "subarachnoid", "sudden severe headache"],
        "procedures": {
            "CT Head without IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "First line imaging to rule out acute subarachnoid hemorrhage."},
            "MRI Brain without IV contrast": {"score": 5, "category": "May Be Appropriate", "notes": "Complementary if CT is negative or equivocal > 6h post-onset."},
            "CT Head with IV contrast": {"score": 2, "category": "Usually Not Appropriate", "notes": "Contrast media can obscure hyperdense acute subarachnoid blood."},
        },
    },
    {
        "indication_keywords": ["pulmonary embolism", "pe", "pleuritic chest pain with dyspnea", "d-dimer positive"],
        "procedures": {
            "CT Pulmonary Angiography (CTPA) Chest with IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "Gold standard definitive imaging for suspected acute PE."},
            "V/Q Scan (Ventilation-Perfusion)": {"score": 8, "category": "Usually Appropriate", "notes": "Preferred alternative if severe renal insufficiency (eGFR < 30) or anaphylactic contrast allergy."},
            "Chest Radiograph (CXR)": {"score": 9, "category": "Usually Appropriate", "notes": "Initial triage examination to exclude pneumothorax or pneumonia."},
            "CT Chest without IV contrast": {"score": 2, "category": "Usually Not Appropriate", "notes": "Cannot visualize pulmonary arterial filling defects without IV contrast."},
        },
    },
    {
        "indication_keywords": ["right lower quadrant pain", "appendicitis", "rlq pain"],
        "procedures": {
            "CT Abdomen and Pelvis with IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "High sensitivity and specificity for adult acute appendicitis."},
            "Ultrasound Abdomen and Pelvis": {"score": 6, "category": "May Be Appropriate", "notes": "First-line preferred modality in pregnant patients and children."},
            "CT Abdomen and Pelvis without contrast": {"score": 7, "category": "Usually Appropriate", "notes": "Acceptable alternative if renal impairment or severe contrast allergy."},
        },
    },
    {
        "indication_keywords": ["acute ischemic stroke", "stroke", "focal neurological deficit", "lvo"],
        "procedures": {
            "CT Head without IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "Essential STAT baseline to exclude acute intracranial hemorrhage prior to thrombolysis."},
            "CT Angiography Head and Neck with IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "Evaluates large vessel occlusion (LVO) for mechanical thrombectomy eligibility."},
            "MRI Brain with DWI/FLAIR": {"score": 8, "category": "Usually Appropriate", "notes": "Highest sensitivity for hyperacute ischemic core."},
        },
    },
    {
        "indication_keywords": ["aortic dissection", "tearing chest pain", "acute aortic syndrome"],
        "procedures": {
            "CT Angiography Chest, Abdomen, Pelvis with IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "Definitive imaging for Stanford Type A vs Type B dissection."},
            "Transesophageal Echocardiography (TEE)": {"score": 8, "category": "Usually Appropriate", "notes": "Rapid bedside assessment for hemodynamically unstable patients."},
            "Chest Radiograph": {"score": 7, "category": "Usually Appropriate", "notes": "Rapid initial screen for mediastinal widening."},
        },
    },
    {
        "indication_keywords": ["uncomplicated low back pain", "lumbar back pain < 6 weeks", "mechanical back pain"],
        "procedures": {
            "MRI Lumbar Spine without IV contrast": {"score": 1, "category": "Usually Not Appropriate", "notes": "Not recommended within first 6 weeks absent red flag signs (fever, trauma, cauda equina)."},
            "Radiography Lumbar Spine": {"score": 2, "category": "Usually Not Appropriate", "notes": "Routine radiography is not recommended for acute uncomplicated low back pain."},
        },
    },
    {
        "indication_keywords": ["osteomyelitis", "suspected bone infection", "diabetic foot ulcer bone"],
        "procedures": {
            "MRI without and with IV contrast": {"score": 9, "category": "Usually Appropriate", "notes": "Most sensitive and specific imaging for early osteomyelitis and marrow edema."},
            "Plain Radiography": {"score": 9, "category": "Usually Appropriate", "notes": "Initial study to exclude foreign bodies, cortical disruption, or gas."},
        },
    },
]

# CT Window Presets
CT_WINDOW_PRESETS: Dict[str, Dict[str, int]] = {
    "LUNG": {"width": 1500, "level": -600},
    "BRAIN": {"width": 80, "level": 40},
    "BONE": {"width": 2000, "level": 500},
    "SOFT_TISSUE": {"width": 350, "level": 40},
    "SUBDURAL_BLOOD": {"width": 150, "level": 75},
    "LIVER": {"width": 150, "level": 30},
}


class RadiologyPreReaderAgent:
    """Production-grade Multimodal Radiology Pre-Reader and Clinical Decision Support Agent."""

    # ── 1. ACR Appropriateness Criteria CDS Engine ───────────────────────────

    def evaluate_acr_appropriateness(
        self,
        clinical_indication: str,
        requested_procedure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Maps clinical indication to ACR Appropriateness Criteria scores (1-9)."""
        ind_lower = clinical_indication.lower()
        matched_rule = None

        for rule in ACR_APPROPRIATENESS_RULES:
            if any(kw in ind_lower for kw in rule["indication_keywords"]):
                matched_rule = rule
                break

        if not matched_rule:
            return {
                "indication": clinical_indication,
                "rule_matched": False,
                "procedures": {},
                "summary": "No specific ACR Appropriateness guideline match found for indication.",
            }

        evaluated_procedures = dict(matched_rule["procedures"])
        requested_eval = None
        if requested_procedure:
            req_lower = requested_procedure.lower()
            for proc_name, data in evaluated_procedures.items():
                if req_lower in proc_name.lower() or proc_name.lower() in req_lower:
                    requested_eval = {"procedure": proc_name, **data}
                    break

        return {
            "indication": clinical_indication,
            "rule_matched": True,
            "evaluated_procedures": evaluated_procedures,
            "requested_procedure_evaluation": requested_eval,
            "highest_rated_procedure": max(
                evaluated_procedures.items(), key=lambda x: x[1]["score"]
            )[0],
        }

    # ── 2. Hounsfield Unit (HU) Attenuation & Windowing Engine ───────────────

    def profile_tissue_density(
        self,
        mean_hu: float,
        std_hu: float = 0.0,
        anatomical_region: str = "HEAD",
    ) -> Dict[str, Any]:
        """Profiles tissue composition and pathology based on physical Hounsfield Unit attenuation."""
        region = anatomical_region.upper()

        if mean_hu <= -900:
            tissue_type = "AIR / GAS"
            category = "HYPODENSE_AIR"
            preset = "LUNG"
            pathology = "Free air, pneumothorax, or normal airway lumina"
        elif -900 < mean_hu <= -400:
            tissue_type = "LUNG PARENCHYMA"
            category = "NORMAL_AERATED_LUNG"
            preset = "LUNG"
            pathology = "Aerated pulmonary parenchyma"
        elif -120 <= mean_hu <= -30:
            tissue_type = "FAT / ADIPOSE TISSUE"
            category = "HYPODENSE_FAT"
            preset = "SOFT_TISSUE"
            pathology = "Adipose tissue, lipoma, or fat-containing lesion (e.g. myelolipoma, angiomyolipoma)"
        elif -20 < mean_hu <= 20:
            tissue_type = "SIMPLE FLUID / WATER / CSF / URINE"
            category = "FLUID_DENSITY"
            preset = "SOFT_TISSUE"
            pathology = "Simple fluid collection, cyst (Bosniak I), ascites, or CSF space"
        elif 20 < mean_hu <= 45:
            tissue_type = "SOFT TISSUE / PARENCHYMA / PROTEINACEOUS FLUID"
            category = "ISODENSE_SOFT_TISSUE"
            preset = "BRAIN" if "HEAD" in region or "BRAIN" in region else "SOFT_TISSUE"
            pathology = "Normal parenchymal organs, muscle, or proteinaceous/exudative collection"
        elif 45 < mean_hu <= 95:
            tissue_type = "ACUTE HEMORRHAGE / CLOTTED BLOOD"
            category = "HYPERDENSE_HEMORRHAGE"
            preset = "SUBDURAL_BLOOD"
            pathology = "Acute clotted hemorrhage, hematoma, or active vascular extravasation"
        elif mean_hu > 250:
            tissue_type = "BONE / CALCIFICATION"
            category = "DENSE_CALCIFICATION"
            preset = "BONE"
            pathology = "Cortical/trabecular bone, dense dystrophic calcification, or surgical hardware"
        else:
            tissue_type = "INDETERMINATE INTERMEDIATE ATTENUATION"
            category = "INDETERMINATE"
            preset = "SOFT_TISSUE"
            pathology = "Intermediate tissue attenuation requiring contrast-enhanced or multiphasic evaluation"

        return {
            "mean_hu": mean_hu,
            "std_hu": std_hu,
            "anatomical_region": region,
            "classified_tissue_type": tissue_type,
            "attenuation_category": category,
            "recommended_window_preset": preset,
            "window_settings": CT_WINDOW_PRESETS.get(preset, {"width": 350, "level": 40}),
            "pathology_interpretation": pathology,
            "is_acute_blood": category == "HYPERDENSE_HEMORRHAGE",
        }

    # ── 3. STAT Critical Alert Trigger Engine ─────────────────────────────────

    def detect_stat_critical_findings(
        self,
        detected_findings: List[str],
        clinical_indication: str = "",
    ) -> Tuple[bool, List[str], str]:
        """Detects life-threatening critical findings requiring immediate verbal alert."""
        text_corpus = (clinical_indication + " " + " ".join(detected_findings)).lower()

        critical_triggers = []

        # 1. Tension Pneumothorax
        if "tension pneumothorax" in text_corpus or ("pneumothorax" in text_corpus and ("shift" in text_corpus or "deviation" in text_corpus)):
            critical_triggers.append("Tension Pneumothorax with hemodynamic compromise / mediastinal shift")

        # 2. Intracranial Hemorrhage / Herniation
        if any(h in text_corpus for h in ["subdural hematoma", "epidural hematoma", "subarachnoid hemorrhage", "intracerebral hemorrhage", "intraparenchymal hemorrhage"]) or (
            "hemorrhage" in text_corpus and ("midline shift" in text_corpus or "herniation" in text_corpus or "mass effect" in text_corpus)
        ):
            critical_triggers.append("Acute Intracranial Hemorrhage / Mass Effect / Impending Herniation")

        # 3. Acute Aortic Dissection
        if "aortic dissection" in text_corpus or "intimal flap" in text_corpus or "ruptured aneurysm" in text_corpus:
            critical_triggers.append("Acute Aortic Dissection / Rupture (Surgical Emergency)")

        # 4. Pulmonary Embolism (Massive / Saddle)
        if "saddle pulmonary embolism" in text_corpus or "massive pulmonary embolism" in text_corpus or ("pulmonary embolism" in text_corpus and ("strain" in text_corpus or "saddle" in text_corpus)):
            critical_triggers.append("Massive / Saddle Pulmonary Embolism with RV Strain")
        elif "pulmonary embolism" in text_corpus or "pneumothorax" in text_corpus or "hemorrhage" in text_corpus:
            critical_triggers.append("Acute Life-Threatening Vascular or Pleural Pathology")

        # 5. Pneumoperitoneum / Free Air
        if "pneumoperitoneum" in text_corpus or "free intraperitoneal air" in text_corpus or "bowel perforation" in text_corpus:
            critical_triggers.append("Pneumoperitoneum (Suspected Viscus Perforation)")

        is_stat = len(critical_triggers) > 0
        urgency = "CRITICAL_STAT" if is_stat else "ROUTINE"
        return is_stat, critical_triggers, urgency

    # ── 4. Standard Preliminary Pre-Read Impression (Backward Compatible) ─────

    def generate_pre_read_impression(
        self,
        modality: str,  # 'CXRAY', 'CT_CHEST', 'MRI_BRAIN', etc.
        clinical_indication: str,
        detected_findings: List[str],
        comparison_prior: Optional[str] = None,
        rads_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates preliminary radiology pre-read impression report."""
        findings_str = "; ".join(detected_findings) if detected_findings else "No acute abnormality detected."
        is_stat, triggers, urgency = self.detect_stat_critical_findings(
            detected_findings, clinical_indication
        )

        comparison_line = f"Comparison: {comparison_prior}\n" if comparison_prior else "Comparison: None available.\n"
        rads_line = f"RADS Assessment: {rads_category}\n" if rads_category else ""

        impression_text = (
            f"PRELIMINARY RADIOLOGY PRE-READ ({modality})\n"
            f"Clinical Indication: {clinical_indication}\n"
            f"{comparison_line}"
            f"Findings: {findings_str}\n"
            f"{rads_line}"
            f"Urgency Status: {urgency}\n"
            f"Disclaimer: Preliminary AI pre-read for triage prioritization. Final verification by Board-Certified Radiologist required.\n"
        )

        return {
            "modality": modality,
            "clinical_indication": clinical_indication,
            "detected_findings": detected_findings,
            "impression_text": impression_text,
            "urgency_level": urgency,
            "requires_stat_radiologist_alert": is_stat,
            "stat_critical_triggers": triggers,
            "status": "PRE_READ_COMPLETED",
        }

    # ── 5. Structured RADS Report & ClinicalAgentResponse Generator ────────────

    def pre_read_and_triage_study(
        self,
        patient_id: str,
        modality: str,
        clinical_indication: str,
        detected_findings: List[str],
        hu_measurements: Optional[List[Dict[str, Any]]] = None,
        comparison_prior: Optional[str] = None,
    ) -> ClinicalAgentResponse:
        """Performs multimodal pre-reading, HU attenuation profiling, and emits structured ClinicalAgentResponse with FHIR proposals."""
        # 1. ACR Appropriateness check
        acr_eval = self.evaluate_acr_appropriateness(clinical_indication, requested_procedure=modality)

        # 2. HU profiling
        hu_profiles = []
        if hu_measurements:
            for meas in hu_measurements:
                prof = self.profile_tissue_density(
                    mean_hu=meas.get("mean_hu", 0.0),
                    std_hu=meas.get("std_hu", 0.0),
                    anatomical_region=meas.get("region", "CHEST"),
                )
                hu_profiles.append(prof)

        # 3. STAT detection and standard impression
        is_stat, triggers, urgency = self.detect_stat_critical_findings(
            detected_findings, clinical_indication
        )

        # Assign RADS category
        if is_stat:
            assigned_rads = "RADS-5 (Critical Acute Life-Threatening Pathology)"
        elif any("suspicious" in f.lower() or "nodule" in f.lower() for f in detected_findings):
            assigned_rads = "RADS-4 (Suspicious Finding - Actionable Follow-up Recommended)"
        elif detected_findings and detected_findings != ["No acute abnormality detected."]:
            assigned_rads = "RADS-2 (Benign Finding)"
        else:
            assigned_rads = "RADS-1 (Negative / Normal Exam)"

        std_impression = self.generate_pre_read_impression(
            modality=modality,
            clinical_indication=clinical_indication,
            detected_findings=detected_findings,
            comparison_prior=comparison_prior,
            rads_category=assigned_rads,
        )

        proposals: List[Any] = []
        recommendations: List[Dict[str, Any]] = []

        recommendations.append({
            "domain": "RADIOLOGY_PRE_READ",
            "modality": modality,
            "urgency": urgency,
            "rads_category": assigned_rads,
            "stat_alert_required": is_stat,
            "acr_appropriateness": acr_eval.get("highest_rated_procedure"),
        })

        # Propose FHIR actions
        if is_stat:
            # STAT Flag Alert
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="clinical_alert",
                    severity="critical",
                    code="722446000",  # Urgent notification needed
                    details=f"STAT RADIOLOGY ALERT: {'; '.join(triggers)}. Immediate verbal physician notification required.",
                    author="RadiologyPreReaderAgent",
                )
            )

            # Service proposals based on critical pathology
            trigger_text = " ".join(triggers).lower()
            if "pneumothorax" in trigger_text:
                proposals.append(
                    FHIRServiceRequestProposal(
                        patient_id=patient_id,
                        category="procedure",
                        code="243144002",  # Tube thoracostomy
                        description="STAT Emergent Tube Thoracostomy / Needle Decompression Consult",
                        urgency="stat",
                        indication="Tension Pneumothorax",
                    )
                )
            elif "intracranial hemorrhage" in trigger_text or "herniation" in trigger_text:
                proposals.append(
                    FHIRServiceRequestProposal(
                        patient_id=patient_id,
                        category="consult",
                        code="306173009",  # Neurosurgery consult
                        description="STAT Emergent Neurosurgery Consultation for Intracranial Hemorrhage",
                        urgency="stat",
                        indication="Acute Intracranial Hemorrhage / Midline Shift",
                    )
                )
                proposals.append(
                    FHIRMedicationRequestProposal(
                        patient_id=patient_id,
                        medication_name="4-Factor Prothrombin Complex Concentrate (Kcentra)",
                        dosage="25-50 units/kg IV once",
                        route="intravenous",
                        frequency="STAT once",
                        indication="Immediate Anticoagulation Reversal for Acute Intracranial Hemorrhage",
                        clinical_evidence=["Intracranial Hemorrhage STAT Alert"],
                        priority="stat",
                    )
                )
            elif "aortic dissection" in trigger_text:
                proposals.append(
                    FHIRServiceRequestProposal(
                        patient_id=patient_id,
                        category="consult",
                        code="306161009",  # Cardiothoracic surgery consult
                        description="STAT Emergent Cardiothoracic & Vascular Surgery Consult",
                        urgency="stat",
                        indication="Acute Aortic Dissection",
                    )
                )
                proposals.append(
                    FHIRMedicationRequestProposal(
                        patient_id=patient_id,
                        medication_name="Labetalol IV or Esmolol Infusion",
                        dosage="Titrate to HR < 60 and SBP 100-120 mmHg",
                        route="intravenous",
                        frequency="continuous infusion",
                        indication="Impulse control / Anti-impulse therapy in Acute Aortic Dissection",
                        clinical_evidence=["Acute Aortic Dissection STAT Alert"],
                        priority="stat",
                    )
                )
        else:
            # Routine service request proposal for formal radiologist reading
            proposals.append(
                FHIRServiceRequestProposal(
                    patient_id=patient_id,
                    category="diagnostic",
                    code="363679005",  # Imaging interpretation
                    description=f"Formal Board-Certified Radiologist Attestation for {modality}",
                    urgency="routine",
                    indication=clinical_indication,
                )
            )

        return ClinicalAgentResponse(
            agent_name="RadiologyPreReaderAgent",
            epistemic_confidence=0.97,
            recommendations=recommendations,
            proposed_fhir_actions=proposals,
            reasoning=(
                f"Preliminary pre-read for {modality} completed with urgency {urgency}. "
                f"RADS Assessment: {assigned_rads}. STAT Alert: {is_stat}."
            ),
            metadata={
                "pre_read_impression": std_impression,
                "acr_appropriateness": acr_eval,
                "hu_profiles": hu_profiles,
            },
        )


# Singleton agent instance
radiology_prereader_agent = RadiologyPreReaderAgent()
