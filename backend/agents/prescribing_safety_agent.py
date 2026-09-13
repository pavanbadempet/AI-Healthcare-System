"""Precision Pharmacotherapy & Toxicology Agent
==============================================
Evaluates multi-drug interactions (DDI), CPIC Level A pharmacogenomics (CYP2C19,
CYP2D6, SLCO1B1, VKORC1, HLA-B*5701), synergistic QT-prolongation (Torsades de
Pointes) and drug-disease contraindications, 2023 AGS Beers Criteria for
geriatric patients (>= 65), and Cockcroft-Gault CrCl dosage adjustment matrix
(Vancomycin, Enoxaparin, DOACs, Cefepime).

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


# ── DRUG-DRUG INTERACTION KNOWLEDGE MATRIX ───────────────────────────────────

DRUG_INTERACTION_MATRIX: Dict[Tuple[str, str], Dict[str, str]] = {
    ("metformin", "contrast"): {
        "severity": "HIGH",
        "type": "METABOLIC_TOXICITY",
        "description": "Metformin with IV iodinated contrast increases risk of lactic acidosis. Hold metformin 48h prior.",
    },
    ("lisinopril", "spironolactone"): {
        "severity": "HIGH",
        "type": "ELECTROLYTE_DISORDER",
        "description": "Combined ACE inhibitor and potassium-sparing diuretic increases severe hyperkalemia risk.",
    },
    ("warfarin", "aspirin"): {
        "severity": "HIGH",
        "type": "HEMORRHAGE_RISK",
        "description": "Concomitant anticoagulant and antiplatelet therapy significantly elevates major bleeding risk.",
    },
    ("warfarin", "nsaids"): {
        "severity": "HIGH",
        "type": "HEMORRHAGE_RISK",
        "description": "NSAIDs damage GI mucosa and displace warfarin from albumin, drastically elevating major upper GI bleed risk.",
    },
    ("methotrexate", "nsaids"): {
        "severity": "CRITICAL",
        "type": "HEMATOLOGIC_TOXICITY",
        "description": "NSAIDs inhibit renal prostaglandin synthesis, reducing methotrexate tubular clearance and triggering fatal pancytopenia.",
    },
    ("simvastatin", "amiodarone"): {
        "severity": "CRITICAL",
        "type": "RHABDOMYOLYSIS",
        "description": "Amiodarone strongly inhibits CYP3A4-mediated simvastatin metabolism, markedly raising systemic exposure and rhabdomyolysis risk (max simvastatin 20mg).",
    },
    ("simvastatin", "diltiazem"): {
        "severity": "HIGH",
        "type": "RHABDOMYOLYSIS",
        "description": "Diltiazem inhibits CYP3A4, substantially increasing simvastatin concentrations (max recommended simvastatin 10mg daily).",
    },
    ("sildenafil", "nitrates"): {
        "severity": "CRITICAL",
        "type": "CARDIOVASCULAR_COLLAPSE",
        "description": "Concurrent PDE-5 inhibitor and nitrate therapy triggers profound, potentially fatal cGMP-mediated refractory hypotension (Absolute Contraindication).",
    },
    ("clopidogrel", "omeprazole"): {
        "severity": "HIGH",
        "type": "THERAPEUTIC_FAILURE",
        "description": "Omeprazole inhibits CYP2C19 bioactivation of clopidogrel into its active antiplatelet metabolite, reducing antiplatelet efficacy by ~45%.",
    },
    ("tramadol", "ssri"): {
        "severity": "HIGH",
        "type": "SEROTONIN_SYNDROME",
        "description": "Combined serotonergic actions increase risk of Serotonin Syndrome (hyperthermia, autonomic hyperreactivity, clonus).",
    },
    ("lithium", "nsaids"): {
        "severity": "HIGH",
        "type": "NEUROTOXICITY",
        "description": "NSAIDs decrease renal lithium excretion, producing dangerous lithium accumulation, tremors, and neurotoxicity.",
    },
    ("ciprofloxacin", "theophylline"): {
        "severity": "HIGH",
        "type": "THEOPHYLLINE_TOXICITY",
        "description": "Ciprofloxacin inhibits CYP1A2 theophylline metabolism, producing severe theophylline toxicity, tachycardia, and seizures.",
    },
}

# Drug Class and Synonym Taxonomy for DDI Expansion
DRUG_CLASS_MAP: Dict[str, List[str]] = {
    "ibuprofen": ["nsaids", "nsaid"],
    "naproxen": ["nsaids", "nsaid"],
    "ketorolac": ["nsaids", "nsaid"],
    "indomethacin": ["nsaids", "nsaid"],
    "meloxicam": ["nsaids", "nsaid"],
    "celecoxib": ["nsaids", "nsaid"],
    "aspirin": ["nsaids", "nsaid", "antiplatelet"],
    "nitroglycerin": ["nitrates", "nitrate"],
    "isosorbide": ["nitrates", "nitrate"],
    "nitroprusside": ["nitrates", "nitrate"],
    "citalopram": ["ssri"],
    "escitalopram": ["ssri"],
    "fluoxetine": ["ssri"],
    "sertraline": ["ssri"],
    "paroxetine": ["ssri"],
    "lisinopril": ["ace_inhibitor", "acei"],
    "enalapril": ["ace_inhibitor", "acei"],
    "ramipril": ["ace_inhibitor", "acei"],
    "spironolactone": ["potassium_sparing_diuretic"],
    "eplerenone": ["potassium_sparing_diuretic"],
}


def _expand_drug_terms(name: str) -> List[str]:
    """Expands drug brand and generic names to include pharmacological class tags."""
    name_clean = name.lower().strip()
    terms = [name_clean]
    for brand, classes in DRUG_CLASS_MAP.items():
        if brand in name_clean:
            terms.extend(classes)
    return terms


# Known QT prolonging agents
QT_PROLONGING_MEDICATIONS = {
    "amiodarone", "sotalol", "dofetilide", "haloperidol", "droperidol",
    "azithromycin", "levofloxacin", "moxifloxacin", "citalopram", "escitalopram",
    "ondansetron", "methadone", "procainamide", "chlorpromazine"
}

# 2023 AGS Beers Criteria List for Geriatrics (Age >= 65)
BEERS_CRITERIA_PIMS = {
    "diphenhydramine": {
        "category": "Anticholinergic / First-gen Antihistamine",
        "rationale": "Highly anticholinergic; clearance reduced in advanced age; risk of confusion, dry mouth, constipation, urinary retention, and falls.",
    },
    "hydroxyzine": {
        "category": "Anticholinergic / First-gen Antihistamine",
        "rationale": "Strong anticholinergic properties; high risk of sedation, confusion, and ataxia.",
    },
    "chlorpheniramine": {
        "category": "Anticholinergic / First-gen Antihistamine",
        "rationale": "Potent anticholinergic activity; elevated delirium and fall risk.",
    },
    "diazepam": {
        "category": "Benzodiazepine",
        "rationale": "Long half-life; older adults have increased sensitivity; elevated risk of cognitive impairment, delirium, falls, and motor vehicle crashes.",
    },
    "lorazepam": {
        "category": "Benzodiazepine",
        "rationale": "Benzodiazepines increase risk of cognitive impairment, delirium, falls, and fractures in older adults.",
    },
    "alprazolam": {
        "category": "Benzodiazepine",
        "rationale": "High risk of dependence, cognitive blunting, ataxia, and hip fractures.",
    },
    "zolpidem": {
        "category": "Nonbenzodiazepine Z-drug Hypnotic",
        "rationale": "Benzodiazepine receptor agonist; adverse events similar to benzodiazepines (delirium, falls, fractures, emergency visits).",
    },
    "amitriptyline": {
        "category": "Tricyclic Antidepressant (TCA)",
        "rationale": "Highly anticholinergic, sedating; causes orthostatic hypotension and cardiac conduction abnormalities.",
    },
    "glyburide": {
        "category": "Long-acting Sulfonylurea",
        "rationale": "Higher risk of severe prolonged hypoglycemia due to active metabolite accumulation with age-related GFR decline.",
    },
    "glimepiride": {
        "category": "Long-acting Sulfonylurea",
        "rationale": "Prolonged half-life in older adults with elevated risk of hypoglycemia.",
    },
    "ketorolac": {
        "category": "Chronic NSAID",
        "rationale": "High risk of gastrointestinal bleeding and peptic ulcer disease; renal toxicity.",
    },
    "indomethacin": {
        "category": "NSAID",
        "rationale": "Adverse CNS effects (headache, confusion) and highest rate of GI adverse effects among NSAIDs.",
    },
}


class PrescribingSafetyAgent:
    """Evaluates prescription safety against patient vitals, renal function, genetics, and DDI."""

    # ── 1. Cockcroft-Gault Renal Clearance Engine ─────────────────────────────

    def calculate_cockcroft_gault_crcl(
        self,
        age_years: float,
        weight_kg: float,
        serum_creatinine_mg_dl: float,
        is_female: bool = False,
    ) -> float:
        """Calculates Creatinine Clearance (CrCl) in mL/min via Cockcroft-Gault formula."""
        if serum_creatinine_mg_dl <= 0 or weight_kg <= 0:
            return 100.0
        crcl = ((140.0 - age_years) * weight_kg) / (72.0 * serum_creatinine_mg_dl)
        if is_female:
            crcl *= 0.85
        return round(crcl, 1)

    def evaluate_renal_dosage_matrix(
        self,
        medication_name: str,
        dosage_mg: float,
        crcl_ml_min: float,
    ) -> Dict[str, Any]:
        """Evaluates renal dose adjustments for Vancomycin, Enoxaparin, DOACs, and Cefepime."""
        med_lower = medication_name.lower()
        adjusted = False
        rec_dose = dosage_mg
        rec_regimen = ""
        warnings = []
        is_contraindicated = False

        # 1. Vancomycin
        if "vancomycin" in med_lower:
            if crcl_ml_min >= 50:
                rec_regimen = "15-20 mg/kg IV q8-12h (Target trough 15-20 ug/mL)"
            elif 30 <= crcl_ml_min < 50:
                rec_regimen = "15-20 mg/kg IV q24h"
                adjusted = True
                warnings.append("CrCl 30-49 mL/min: Extended interval to q24h required to avoid nephrotoxicity.")
            elif 15 <= crcl_ml_min < 30:
                rec_regimen = "15-20 mg/kg IV q48h"
                adjusted = True
                warnings.append("CrCl 15-29 mL/min: Extended interval to q48h required with daily trough monitoring.")
            else:
                rec_regimen = "15-25 mg/kg IV single loading dose; redose only when serum trough < 15-20 ug/mL"
                adjusted = True
                warnings.append("CrCl < 15 mL/min / Dialysis: Strict trough-guided redosing protocol.")

        # 2. Enoxaparin (Lovenox)
        elif "enoxaparin" in med_lower or "lovenox" in med_lower:
            if crcl_ml_min < 30.0:
                adjusted = True
                # If therapeutic dosing (~1 mg/kg q12h), reduce to 1 mg/kg q24h
                if dosage_mg > 40.0:
                    rec_regimen = f"{dosage_mg} mg SubQ every 24 hours (reduced from q12h)"
                    warnings.append("Severe Renal Impairment (CrCl < 30 mL/min): Enoxaparin therapeutic treatment dose must be reduced to 1 mg/kg ONCE daily (q24h) to avoid bioaccumulation and major hemorrhage.")
                else:
                    rec_dose = min(dosage_mg, 30.0)
                    rec_regimen = "30 mg SubQ once daily (q24h)"
                    warnings.append("Severe Renal Impairment (CrCl < 30 mL/min): Enoxaparin DVT prophylaxis dose must be reduced from 40mg to 30mg once daily.")

        # 3. Cefepime
        elif "cefepime" in med_lower:
            if crcl_ml_min >= 50:
                rec_regimen = "2g IV every 8 hours"
            elif 30 <= crcl_ml_min < 50:
                rec_regimen = "2g IV every 12 hours"
                adjusted = True
                warnings.append("CrCl 30-49 mL/min: Reduce Cefepime frequency to 2g IV q12h to prevent neurotoxicity.")
            elif 11 <= crcl_ml_min < 30:
                rec_regimen = "2g IV every 24 hours"
                adjusted = True
                warnings.append("CrCl 11-29 mL/min: Reduce Cefepime frequency to 2g IV q24h.")
            else:
                rec_regimen = "1g IV every 24 hours"
                adjusted = True
                warnings.append("CRITICAL: CrCl < 11 mL/min: Cefepime dose must be restricted to 1g IV q24h. Unadjusted cefepime in renal impairment causes severe neurotoxicity, encephalopathy, and nonconvulsive status epilepticus.")

        # 4. DOACs: Rivaroxaban (Xarelto)
        elif "rivaroxaban" in med_lower or "xarelto" in med_lower:
            if crcl_ml_min < 15.0:
                is_contraindicated = True
                warnings.append("CrCl < 15 mL/min: Rivaroxaban is CONTRAINDICATED due to unpredictable clearance and high fatal bleed risk.")
            elif 15.0 <= crcl_ml_min <= 50.0:
                adjusted = True
                rec_dose = 15.0
                rec_regimen = "15 mg PO once daily with evening meal"
                warnings.append("CrCl 15-50 mL/min: Rivaroxaban AF dose must be adjusted down from 20mg to 15mg once daily.")

        # 5. DOACs: Apixaban (Eliquis)
        elif "apixaban" in med_lower or "eliquis" in med_lower:
            if crcl_ml_min < 15.0:
                warnings.append("CrCl < 15 mL/min: Apixaban clinical data limited; use with extreme caution or avoid.")

        # 6. DOACs: Dabigatran (Pradaxa)
        elif "dabigatran" in med_lower or "pradaxa" in med_lower:
            if crcl_ml_min < 15.0:
                is_contraindicated = True
                warnings.append("CrCl < 15 mL/min: Dabigatran is CONTRAINDICATED.")
            elif 15.0 <= crcl_ml_min < 30.0:
                adjusted = True
                rec_dose = 75.0
                rec_regimen = "75 mg PO twice daily"
                warnings.append("CrCl 15-29 mL/min: Dabigatran dose must be reduced to 75mg PO BID.")

        # 7. Metformin
        elif "metformin" in med_lower:
            if crcl_ml_min < 30.0:
                is_contraindicated = True
                warnings.append(f"CrCl/eGFR < 30 mL/min ({crcl_ml_min}): Metformin is CONTRAINDICATED due to high risk of lactic acidosis.")
            elif 30.0 <= crcl_ml_min < 45.0:
                adjusted = True
                rec_dose = min(dosage_mg, 500.0)
                rec_regimen = "500 mg PO daily (maximum)"
                warnings.append("CrCl/eGFR 30-44 mL/min: Max recommended Metformin dose is 500mg daily. Do not initiate new therapy.")

        return {
            "medication": medication_name,
            "dosage_adjusted": adjusted,
            "is_contraindicated": is_contraindicated,
            "recommended_dosage_mg": rec_dose,
            "recommended_regimen": rec_regimen,
            "renal_warnings": warnings,
        }

    # ── 2. Pharmacogenomics (CPIC Level A) Engine ─────────────────────────────

    def evaluate_pharmacogenomics(
        self,
        medication_name: str,
        patient_genotypes: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Evaluates CPIC Level A guidelines for CYP2C19, CYP2D6, SLCO1B1, VKORC1, HLA-B*5701."""
        med_lower = medication_name.lower()
        findings = []

        # 1. CYP2C19 & Clopidogrel (Plavix)
        cyp2c19 = patient_genotypes.get("cyp2c19", "").lower().replace(" ", "")
        if "clopidogrel" in med_lower or "plavix" in med_lower:
            if any(pm in cyp2c19 for pm in ["*2/*2", "*2/*3", "*3/*3", "poor"]):
                findings.append({
                    "gene": "CYP2C19",
                    "phenotype": "Poor Metabolizer",
                    "actionability": "CPIC_LEVEL_A_ACTIONABLE",
                    "severity": "CRITICAL",
                    "recommendation": "Avoid clopidogrel. Significantly reduced active antiplatelet metabolite formation; high risk of stent thrombosis and major adverse cardiovascular events (MACE). Prescribe alternative P2Y12 inhibitor (e.g. Prasugrel 10mg daily or Ticagrelor 90mg BID) unless contraindicated.",
                })

        # 2. CYP2D6 & Codeine / Tramadol
        cyp2d6 = patient_genotypes.get("cyp2d6", "").lower().replace(" ", "")
        if any(op in med_lower for op in ["codeine", "tramadol"]):
            if any(um in cyp2d6 for um in ["*1/*1xn", "*1/*2xn", "*2/*2xn", "ultrarapid"]):
                findings.append({
                    "gene": "CYP2D6",
                    "phenotype": "Ultrarapid Metabolizer",
                    "actionability": "CPIC_LEVEL_A_ACTIONABLE",
                    "severity": "CRITICAL",
                    "recommendation": "Avoid codeine and tramadol. Markedly enhanced conversion to morphine/active metabolite; high risk of severe or fatal respiratory depression even at therapeutic doses. Use non-codeine opioid (e.g. morphine, hydromorphone) at adjusted doses.",
                })
            elif any(pm in cyp2d6 for pm in ["*3/*4", "*4/*4", "*5/*5", "*4/*5", "poor"]):
                findings.append({
                    "gene": "CYP2D6",
                    "phenotype": "Poor Metabolizer",
                    "actionability": "CPIC_LEVEL_A_ACTIONABLE",
                    "severity": "HIGH",
                    "recommendation": "Avoid codeine and tramadol. Inability to bioactivate prodrug to active analgesic metabolite; risk of therapeutic failure and unmanaged severe pain. Use alternative non-CYP2D6 analgesic.",
                })

        # 3. SLCO1B1 & Simvastatin
        slco1b1 = patient_genotypes.get("slco1b1", "").lower().replace(" ", "")
        if "simvastatin" in med_lower:
            if any(pf in slco1b1 for pf in ["521cc", "*5/*5", "*15/*15", "poor"]):
                findings.append({
                    "gene": "SLCO1B1",
                    "phenotype": "Poor Function (521CC / *5/*5)",
                    "actionability": "CPIC_LEVEL_A_ACTIONABLE",
                    "severity": "CRITICAL",
                    "recommendation": "Avoid simvastatin (especially > 20mg). Markedly reduced hepatic OATP1B1 uptake causes up to 221% higher systemic plasma concentrations of simvastatin acid, resulting in severe myopathy and rhabdomyolysis. Switch to Rosuvastatin or Pravastatin at conservative doses.",
                })

        # 4. VKORC1 / CYP2C9 & Warfarin
        vkorc1 = patient_genotypes.get("vkorc1", "").lower().replace(" ", "")
        if "warfarin" in med_lower:
            if any(v in vkorc1 for v in ["-1639g>a", "aa", "variant"]):
                findings.append({
                    "gene": "VKORC1",
                    "phenotype": "-1639G>A AA Genotype (High Sensitivity)",
                    "actionability": "CPIC_LEVEL_A_ACTIONABLE",
                    "severity": "HIGH",
                    "recommendation": "Patient possesses VKORC1 warfarin-hypersensitive genotype. Standard starting doses cause rapid supratherapeutic INR and catastrophic hemorrhage. Reduce initial weekly warfarin dose by 50-70% with close INR monitoring.",
                })

        # 5. HLA-B*5701 & Abacavir
        hla_b_5701 = patient_genotypes.get("hla_b_5701", "").lower()
        if "abacavir" in med_lower:
            if "positive" in hla_b_5701 or "detected" in hla_b_5701:
                findings.append({
                    "gene": "HLA-B*5701",
                    "phenotype": "Positive / Carrier",
                    "actionability": "CPIC_LEVEL_A_CONTRAINDICATION",
                    "severity": "CRITICAL",
                    "recommendation": "ABSOLUTE CONTRAINDICATION: Patient is HLA-B*5701 positive. Severe, potentially fatal multisystem Abacavir Hypersensitivity Reaction (AHR) occurs upon exposure. Do not prescribe or administer abacavir.",
                })

        return findings

    # ── 3. Synergistic QT Prolongation & Drug-Disease Engine ───────────────────

    def evaluate_qt_and_drug_disease_risk(
        self,
        candidate_medication: str,
        active_medications: List[str],
        baseline_qtc_ms: Optional[float] = None,
        serum_potassium_meq_l: Optional[float] = None,
        serum_magnesium_mg_dl: Optional[float] = None,
        patient_conditions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluates synergistic QT prolongation (Torsades de Pointes) and drug-disease contraindications."""
        cand_lower = candidate_medication.lower()
        active_lowers = [m.lower() for m in active_medications]
        all_meds = [cand_lower] + active_lowers
        conditions = [c.lower() for c in (patient_conditions or [])]

        # 1. Identify QT prolonging drugs
        qt_drugs_found = []
        for m in all_meds:
            for qt_drug in QT_PROLONGING_MEDICATIONS:
                if qt_drug in m and qt_drug not in qt_drugs_found:
                    qt_drugs_found.append(qt_drug)

        qt_risk_level = "LOW"
        qt_warnings = []

        if len(qt_drugs_found) >= 2:
            qt_risk_level = "HIGH"
            qt_warnings.append(
                f"Synergistic QT Prolongation: Multiple QT-prolonging agents active ({', '.join(qt_drugs_found)}). "
                "Substantially elevated risk of Torsades de Pointes (TdP) and fatal ventricular arrhythmias."
            )
        elif len(qt_drugs_found) == 1:
            qt_risk_level = "MODERATE"
            qt_warnings.append(f"Contains QT-prolonging agent: {qt_drugs_found[0]}.")

        # Compounding factors: baseline QTc
        if baseline_qtc_ms is not None:
            if baseline_qtc_ms >= 500.0:
                qt_risk_level = "CRITICAL"
                qt_warnings.append(f"Critical baseline QTc prolongation ({baseline_qtc_ms} ms >= 500 ms). Extreme risk of TdP.")
            elif baseline_qtc_ms >= 460.0 and len(qt_drugs_found) >= 1:
                qt_risk_level = "HIGH"
                qt_warnings.append(f"Prolonged baseline QTc ({baseline_qtc_ms} ms). Caution with QT-prolonging drugs.")

        # Compounding factors: electrolytes
        if serum_potassium_meq_l is not None and serum_potassium_meq_l < 3.5:
            qt_warnings.append(f"Hypokalemia detected ({serum_potassium_meq_l} mEq/L < 3.5): Potentiates drug-induced Torsades de Pointes.")
            if len(qt_drugs_found) >= 1:
                qt_risk_level = "HIGH"
        if serum_magnesium_mg_dl is not None and serum_magnesium_mg_dl < 1.7:
            qt_warnings.append(f"Hypomagnesemia detected ({serum_magnesium_mg_dl} mg/dL < 1.7): Impairs cardiac repolarization.")

        # 2. Drug-Disease Contraindications
        disease_contraindications = []
        if any("asthma" in c or "bronchospasm" in c for c in conditions):
            if any(bb in cand_lower for bb in ["propranolol", "nadolol", "timolol", "carvedilol", "labetalol"]):
                disease_contraindications.append({
                    "condition": "Severe Asthma / Reactive Airway",
                    "drug": candidate_medication,
                    "severity": "CRITICAL",
                    "message": "Non-selective beta-blockers trigger life-threatening bronchospasm in active asthma.",
                })

        if any("heart failure" in c or "chf" in c for c in conditions):
            if any(ns in cand_lower for ns in ["ibuprofen", "naproxen", "ketorolac", "indomethacin", "meloxicam"]):
                disease_contraindications.append({
                    "condition": "Heart Failure",
                    "drug": candidate_medication,
                    "severity": "HIGH",
                    "message": "NSAIDs cause renal sodium/water retention, blunting loop diuretics and triggering acute decompensated heart failure.",
                })

        if any("glaucoma" in c for c in conditions):
            if any(ac in cand_lower for ac in ["amitriptyline", "diphenhydramine", "oxybutynin", "scopolamine"]):
                disease_contraindications.append({
                    "condition": "Narrow-Angle Glaucoma",
                    "drug": candidate_medication,
                    "severity": "HIGH",
                    "message": "Anticholinergics cause pupillary dilation and may precipitate acute angle-closure glaucoma.",
                })

        return {
            "qt_prolonging_drugs_active": qt_drugs_found,
            "qt_risk_level": qt_risk_level,
            "qt_warnings": qt_warnings,
            "drug_disease_contraindications": disease_contraindications,
        }

    # ── 4. Beers Criteria (2023 AGS) Geriatric Engine ─────────────────────────

    def evaluate_beers_criteria(
        self,
        medication_name: str,
        patient_age_years: float,
    ) -> Optional[Dict[str, Any]]:
        """Evaluates 2023 AGS Beers Criteria for Potentially Inappropriate Medications (PIMs) in age >= 65."""
        if patient_age_years < 65.0:
            return None

        med_lower = medication_name.lower()
        for pim_drug, details in BEERS_CRITERIA_PIMS.items():
            if pim_drug in med_lower:
                return {
                    "is_beers_pim": True,
                    "medication": medication_name,
                    "patient_age": patient_age_years,
                    "category": details["category"],
                    "rationale": details["rationale"],
                    "severity": "HIGH",
                    "recommendation": f"Avoid prescribing {medication_name} in older adults (age >= 65) per 2023 AGS Beers Criteria. Consider safer alternatives.",
                }
        return None

    # ── 5. Standard Prescription Safety Evaluator (Backward Compatible) ────────

    def evaluate_prescription_safety(
        self,
        medication_name: str,
        dosage_mg: float,
        egfr: Optional[float] = None,
        active_medications: Optional[List[str]] = None,
        patient_age_years: float = 45.0,
        patient_weight_kg: float = 70.0,
        serum_creatinine_mg_dl: Optional[float] = None,
        is_female: bool = False,
        patient_genotypes: Optional[Dict[str, str]] = None,
        baseline_qtc_ms: Optional[float] = None,
        serum_potassium: Optional[float] = None,
        patient_conditions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluates comprehensive prescription safety (DDI, CPIC, Beers, CrCl, QT)."""
        active_meds = [m.lower() for m in (active_medications or [])]
        warnings = []
        dosage_adjusted = False
        recommended_dosage_mg = dosage_mg

        # 1. Renal Clearance / eGFR evaluation
        crcl = egfr
        if serum_creatinine_mg_dl is not None:
            crcl = self.calculate_cockcroft_gault_crcl(
                age_years=patient_age_years,
                weight_kg=patient_weight_kg,
                serum_creatinine_mg_dl=serum_creatinine_mg_dl,
                is_female=is_female,
            )

        if crcl is not None:
            renal_eval = self.evaluate_renal_dosage_matrix(medication_name, dosage_mg, crcl)
            if renal_eval["dosage_adjusted"]:
                dosage_adjusted = True
                recommended_dosage_mg = renal_eval["recommended_dosage_mg"]
            if renal_eval["is_contraindicated"]:
                warnings.append({
                    "type": "RENAL_CONTRAINDICATION",
                    "severity": "CRITICAL",
                    "message": "; ".join(renal_eval["renal_warnings"]),
                })
            elif renal_eval["renal_warnings"]:
                for rw in renal_eval["renal_warnings"]:
                    warnings.append({
                        "type": "RENAL_DOSAGE_ADJUSTMENT",
                        "severity": "WARNING",
                        "message": rw,
                    })

        # 2. Drug-Drug Interaction Matrix
        med_terms = _expand_drug_terms(medication_name)
        for active in active_meds:
            act_terms = _expand_drug_terms(active)
            for (d1, d2), info in DRUG_INTERACTION_MATRIX.items():
                match = any(d1 in mt and d2 in at for mt in med_terms for at in act_terms) or \
                        any(d2 in mt and d1 in at for mt in med_terms for at in act_terms)
                if match:
                    warnings.append({
                        "type": "DRUG_INTERACTION",
                        "severity": info["severity"],
                        "message": f"Interaction detected between {medication_name} and {active.title()}: {info['description']}",
                    })

        # 3. Pharmacogenomics (CPIC)
        if patient_genotypes:
            cpic_findings = self.evaluate_pharmacogenomics(medication_name, patient_genotypes)
            for cf in cpic_findings:
                warnings.append({
                    "type": "PHARMACOGENOMIC_GUIDELINE",
                    "severity": cf["severity"],
                    "message": f"CPIC Guideline ({cf['gene']} - {cf['phenotype']}): {cf['recommendation']}",
                })

        # 4. Beers Criteria
        beers_finding = self.evaluate_beers_criteria(medication_name, patient_age_years)
        if beers_finding:
            warnings.append({
                "type": "BEERS_CRITERIA_GERIATRIC",
                "severity": "HIGH",
                "message": f"2023 AGS Beers Criteria: {beers_finding['rationale']}",
            })

        # 5. QT Prolongation & Drug-Disease
        qt_disease = self.evaluate_qt_and_drug_disease_risk(
            candidate_medication=medication_name,
            active_medications=active_meds,
            baseline_qtc_ms=baseline_qtc_ms,
            serum_potassium_meq_l=serum_potassium,
            patient_conditions=patient_conditions,
        )
        if qt_disease["qt_risk_level"] in ["HIGH", "CRITICAL"]:
            warnings.append({
                "type": "QT_PROLONGATION_RISK",
                "severity": "HIGH",
                "message": "; ".join(qt_disease["qt_warnings"]),
            })
        for dd in qt_disease["drug_disease_contraindications"]:
            warnings.append({
                "type": "DRUG_DISEASE_CONTRAINDICATION",
                "severity": dd["severity"],
                "message": f"Contraindication ({dd['condition']}): {dd['message']}",
            })

        has_critical = any(w["severity"] in ["CRITICAL", "HIGH"] for w in warnings)

        return {
            "medication": medication_name,
            "original_dosage_mg": dosage_mg,
            "recommended_dosage_mg": recommended_dosage_mg,
            "dosage_adjusted": dosage_adjusted,
            "safety_status": "REJECTED" if has_critical else ("WARNING" if warnings else "SAFE"),
            "warnings": warnings,
        }

    # ── 6. Structured ClinicalAgentResponse Generator ─────────────────────────

    def evaluate_clinical_pharmacotherapy(
        self,
        patient_id: str,
        medication_name: str,
        dosage_mg: float,
        route: str = "oral",
        frequency: str = "daily",
        indication: str = "",
        patient_age_years: float = 45.0,
        patient_weight_kg: float = 70.0,
        serum_creatinine_mg_dl: Optional[float] = None,
        egfr: Optional[float] = None,
        is_female: bool = False,
        active_medications: Optional[List[str]] = None,
        patient_genotypes: Optional[Dict[str, str]] = None,
        baseline_qtc_ms: Optional[float] = None,
        serum_potassium: Optional[float] = None,
        patient_conditions: Optional[List[str]] = None,
    ) -> ClinicalAgentResponse:
        """Executes full pharmacotherapy analysis and emits structured ClinicalAgentResponse with FHIR proposals."""
        safety_eval = self.evaluate_prescription_safety(
            medication_name=medication_name,
            dosage_mg=dosage_mg,
            egfr=egfr,
            active_medications=active_medications,
            patient_age_years=patient_age_years,
            patient_weight_kg=patient_weight_kg,
            serum_creatinine_mg_dl=serum_creatinine_mg_dl,
            is_female=is_female,
            patient_genotypes=patient_genotypes,
            baseline_qtc_ms=baseline_qtc_ms,
            serum_potassium=serum_potassium,
            patient_conditions=patient_conditions,
        )

        proposals: List[Any] = []
        recommendations: List[Dict[str, Any]] = []

        recommendations.append({
            "domain": "PRESCRIBING_SAFETY",
            "medication": medication_name,
            "status": safety_eval["safety_status"],
            "original_dose_mg": dosage_mg,
            "recommended_dose_mg": safety_eval["recommended_dosage_mg"],
            "dosage_adjusted": safety_eval["dosage_adjusted"],
            "warning_count": len(safety_eval["warnings"]),
        })

        # Build FHIR proposals based on warnings
        for w in safety_eval["warnings"]:
            sev = "critical" if w["severity"] in ["CRITICAL", "HIGH"] else "warning"
            proposals.append(
                FHIRFlagProposal(
                    patient_id=patient_id,
                    status="active",
                    category="clinical_alert",
                    severity=sev,
                    code="419099009",  # Pharmacotherapy alert
                    details=f"[{w['type']}] {w['message']}",
                    author="PrescribingSafetyAgent",
                )
            )

        # If rejected, propose alternate medication or TDM service request
        if safety_eval["safety_status"] == "REJECTED":
            if "clopidogrel" in medication_name.lower():
                proposals.append(
                    FHIRMedicationRequestProposal(
                        patient_id=patient_id,
                        medication_name="Ticagrelor",
                        dosage="90 mg",
                        route="oral",
                        frequency="twice daily",
                        indication="Alternative P2Y12 inhibitor for CYP2C19 Poor Metabolizer",
                        clinical_evidence=["CPIC Clopidogrel-CYP2C19 Level A Guideline"],
                    )
                )
            elif "vancomycin" in medication_name.lower():
                proposals.append(
                    FHIRServiceRequestProposal(
                        patient_id=patient_id,
                        category="laboratory",
                        code="34565-2",  # LOINC: Vancomycin trough
                        description="Therapeutic Drug Monitoring: Serum Vancomycin Trough Level",
                        urgency="stat",
                        indication="Renal failure vancomycin dosing adjustment",
                    )
                )
        else:
            # Safe or adjusted order
            final_dose_str = f"{safety_eval['recommended_dosage_mg']} mg"
            proposals.append(
                FHIRMedicationRequestProposal(
                    patient_id=patient_id,
                    medication_name=medication_name,
                    dosage=final_dose_str,
                    route=route,
                    frequency=frequency,
                    indication=indication,
                    clinical_evidence=["Approved by PrescribingSafetyAgent"],
                )
            )

        return ClinicalAgentResponse(
            agent_name="PrescribingSafetyAgent",
            epistemic_confidence=0.96,
            recommendations=recommendations,
            proposed_fhir_actions=proposals,
            reasoning=(
                f"Prescription safety audit completed for {medication_name} {dosage_mg}mg: "
                f"Status {safety_eval['safety_status']} with {len(safety_eval['warnings'])} warnings. "
                f"Recommended dose: {safety_eval['recommended_dosage_mg']}mg."
            ),
            metadata={"safety_evaluation": safety_eval},
        )


# Singleton instance
prescribing_safety_agent = PrescribingSafetyAgent()
