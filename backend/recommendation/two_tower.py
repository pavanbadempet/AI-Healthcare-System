"""
Stage 1: Two-Tower Candidate Retrieval Engine.
Encodes Patient & Item representations into dense embedding space and retrieves top-K candidates via ANN search.
"""

import math
import logging
from typing import List, Dict, Any, Optional
from backend.schemas.recommendation import PatientContext, CandidateItem
from backend.core_ai import embed_text

logger = logging.getLogger("backend.recommendation.two_tower")


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class ClinicalKnowledgeUniverse:
    """In-memory repository of evidence-based clinical interventions, trials, and lifestyle pathways."""
    
    _INSTANCES: Dict[str, List[Dict[str, Any]]] = {
        "clinical_intervention": [
            {
                "item_id": "MED-SGLT2-01",
                "title": "SGLT2 Inhibitor Therapy (Empagliflozin / Dapagliflozin)",
                "category": "pharmacotherapy",
                "description": "Cardiorenal protective glucose-lowering therapy recommended for Type 2 Diabetes with CKD or Heart Failure risk.",
                "evidence_level": "Level 1A (ADA/ESC Guidelines)",
                "contraindications": ["severe renal impairment eGFR < 20", "history of euglycemic DKA"],
                "tags": ["diabetes", "heart_failure", "ckd", "cardiovascular", "hypertension"]
            },
            {
                "item_id": "MED-GLP1-02",
                "title": "GLP-1 Receptor Agonist (Semaglutide / Liraglutide)",
                "category": "pharmacotherapy",
                "description": "Incretin mimetic promoting glycemic control, weight reduction, and MACE reduction in diabetic patients.",
                "evidence_level": "Level 1A (AACE/ACC)",
                "contraindications": ["medullary thyroid carcinoma", "multiple endocrine neoplasia syndrome type 2"],
                "tags": ["diabetes", "obesity", "mace", "weight_loss", "cardiovascular"]
            },
            {
                "item_id": "MED-ACEI-03",
                "title": "ACE Inhibitor / ARB Renoprotective Regimen (Lisinopril / Losartan)",
                "category": "pharmacotherapy",
                "description": "First-line antihypertensive therapy reducing intraglomerular pressure and microalbuminuria.",
                "evidence_level": "Level 1A (KDIGO)",
                "contraindications": ["pregnancy", "bilateral renal artery stenosis", "angioedema"],
                "tags": ["hypertension", "ckd", "proteinuria", "heart_failure", "nephrology"]
            },
            {
                "item_id": "MED-STATIN-04",
                "title": "High-Intensity Statin Therapy (Atorvastatin 40-80mg)",
                "category": "pharmacotherapy",
                "description": "Primary and secondary ASCVD prevention, lowering LDL-C and stabilizing vascular plaques.",
                "evidence_level": "Level 1A (AHA/ACC)",
                "contraindications": ["active liver failure", "unexplained persistent transaminase elevations", "pregnancy"],
                "tags": ["hyperlipidemia", "cardiovascular", "ascvd", "stroke", "atherosclerosis"]
            },
            {
                "item_id": "DIAG-CORONARY-05",
                "title": "Coronary CT Angiography (CCTA) & CAC Scoring",
                "category": "diagnostics",
                "description": "Non-invasive anatomical assessment of coronary artery plaque burden in intermediate ASCVD risk.",
                "evidence_level": "Level 1B",
                "contraindications": ["severe iodinated contrast allergy", "decompensated renal failure without dialysis"],
                "tags": ["cardiology", "chest_pain", "cac", "plaque", "imaging"]
            },
            {
                "item_id": "DIAG-FIBROSCAN-06",
                "title": "Transient Elastography (FibroScan) for NAFLD/MASH",
                "category": "diagnostics",
                "description": "Quantitative acoustic ultrasound evaluating hepatic steatosis and liver fibrosis staging.",
                "evidence_level": "Level 1B (AASLD)",
                "contraindications": ["active ascites", "implanted electronic cardiac devices in path"],
                "tags": ["liver", "nafld", "mash", "hepatology", "steatosis"]
            },
            {
                "item_id": "PULM-SPIRO-07",
                "title": "Low-Dose Chest CT (LDCT) Lung Cancer Screening",
                "category": "screening",
                "description": "Annual low-dose helical computed tomography for high-risk smokers meeting USPSTF criteria.",
                "evidence_level": "Level 1A (USPSTF)",
                "contraindications": ["severe acute pulmonary infection", "patient unwilling to undergo curative surgery"],
                "tags": ["lung_cancer", "smoking", "pulmonology", "screening", "nodule"]
            },
            {
                "item_id": "RENAL-EVAL-08",
                "title": "Spot Urinary Albumin-to-Creatinine Ratio (uACR) & eGFR Trend",
                "category": "diagnostics",
                "description": "Longitudinal surveillance of glomerular barrier function and nephron preservation.",
                "evidence_level": "Level 1A (KDIGO)",
                "contraindications": ["heavy menstrual bleeding", "acute urinary tract infection at sample time"],
                "tags": ["ckd", "kidney", "nephrology", "microalbuminuria", "diabetes"]
            }
        ],
        "lifestyle_pathway": [
            {
                "item_id": "LIFE-MED-DIET-01",
                "title": "Mediterranean Dietary Pattern & Polyphenol Enrichment",
                "category": "nutrition",
                "description": "Anti-inflammatory dietary protocol rich in extra virgin olive oil, nuts, legumes, and omega-3 fatty acids.",
                "evidence_level": "Level 1A (PREDIMED Study)",
                "contraindications": ["specific nut or seafood severe anaphylaxis"],
                "tags": ["hypertension", "diabetes", "cardiovascular", "dyslipidemia", "gut_health"]
            },
            {
                "item_id": "LIFE-ZONE2-CARDIO-02",
                "title": "Zone 2 Mitochondrial Endurance Protocol (150-180 min/week)",
                "category": "exercise",
                "description": "Steady-state aerobic exertion below aerobic threshold to optimize fat oxidation and metabolic flexibility.",
                "evidence_level": "Level 1A (ACSM)",
                "contraindications": ["unstable angina", "decompensated aortic stenosis", "acute myocarditis"],
                "tags": ["cardiovascular", "insulin_resistance", "endurance", "metabolic", "hypertension"]
            },
            {
                "item_id": "LIFE-CIRCADIAN-03",
                "title": "Circadian Sleep Architecture & REM Optimization",
                "category": "sleep_hygiene",
                "description": "Behavioral alignment of core sleep window (7-9 hours) with morning bright light exposure (10,000 lux).",
                "evidence_level": "Level 1B",
                "contraindications": ["bipolar mania with light sensitivity"],
                "tags": ["sleep", "cortisol", "hypertension", "stress", "mental_health"]
            },
            {
                "item_id": "LIFE-STRENGTH-04",
                "title": "Progressive Resistance Training (Hypertrophy & Bone Density)",
                "category": "exercise",
                "description": "Multi-joint compound movements (2-3x weekly) preserving lean sarcopenic muscle mass and insulin sensitivity.",
                "evidence_level": "Level 1A",
                "contraindications": ["acute fracture", "unrepaired abdominal aortic aneurysm > 5cm"],
                "tags": ["sarcopenia", "osteoporosis", "diabetes", "strength", "longevity"]
            }
        ],
        "clinical_trial": [
            {
                "item_id": "TRIAL-CAR-T-01",
                "title": "NCT05912831: Allogeneic CD19/CD22 Dual-Targeting CAR-T in Refractory B-Cell Malignancies",
                "category": "oncology_immunotherapy",
                "description": "Phase 2 multi-center investigation evaluating persistence and safety of gene-edited allogeneic CAR-T cells.",
                "evidence_level": "Phase 2 Investigational",
                "contraindications": ["active uncontrolled systemic fungal infection", "severe cardiac ejection fraction < 30%"],
                "tags": ["oncology", "car_t", "hematology", "immunotherapy", "clinical_trial"]
            },
            {
                "item_id": "TRIAL-CRISPR-02",
                "title": "NCT04874982: In Vivo Base Editing for Heterozygous Familial Hypercholesterolemia",
                "category": "genomic_medicine",
                "description": "Phase 1/2 clinical study assessing targeted PCSK9 silencing via lipid nanoparticle-delivered adenine base editors.",
                "evidence_level": "Phase 1/2 Investigational",
                "contraindications": ["cirrhosis Child-Pugh Class C", "known hypersensitivity to lipid nanoparticles"],
                "tags": ["genomics", "crispr", "hypercholesterolemia", "cardiovascular", "clinical_trial"]
            },
            {
                "item_id": "TRIAL-ALZ-03",
                "title": "NCT06118942: Monoclonal Antibody Targeting Soluble Amyloid Oligomers in Early MCI",
                "category": "neurology",
                "description": "Double-blind, placebo-controlled Phase 3 trial measuring cognitive preservation and microglial activation markers.",
                "evidence_level": "Phase 3 Investigational",
                "contraindications": ["more than 4 microhemorrhages on baseline MRI", "concurrent anticoagulation therapy"],
                "tags": ["alzheimers", "neurology", "mci", "cognitive", "clinical_trial"]
            }
        ]
    }

    @classmethod
    def get_items_for_domain(cls, domain: str) -> List[Dict[str, Any]]:
        return cls._INSTANCES.get(domain, cls._INSTANCES["clinical_intervention"])


class TwoTowerCandidateRetrieval:
    """
    Two-Tower Candidate Generation:
    - User/Patient Tower: Synthesizes rich clinical summary text & vectorizes it.
    - Item Tower: Pre-vectorized catalog of clinical interventions.
    """

    def __init__(self):
        self._item_embeddings_cache: Dict[str, List[float]] = {}

    def _build_patient_representation_text(self, context: PatientContext) -> str:
        """Constructs a dense clinical narrative representing the patient."""
        parts = [
            f"Patient Age: {context.age} years old, Gender: {context.gender}.",
        ]
        if context.bmi:
            parts.append(f"BMI: {context.bmi:.1f} kg/m2.")
        if context.systolic_bp and context.diastolic_bp:
            parts.append(f"Blood Pressure: {context.systolic_bp:.0f}/{context.diastolic_bp:.0f} mmHg.")
        if context.fasting_glucose:
            parts.append(f"Fasting Blood Glucose: {context.fasting_glucose:.0f} mg/dL.")
        if context.hba1c:
            parts.append(f"HbA1c: {context.hba1c:.1f}%.")
        if context.primary_conditions:
            parts.append(f"Diagnoses: {', '.join(context.primary_conditions)}.")
        if context.current_medications:
            parts.append(f"Active Medications: {', '.join(context.current_medications)}.")
        if context.recent_interactions:
            parts.append(f"Recent Topics: {', '.join(context.recent_interactions)}.")
        return " ".join(parts)

    def _build_item_representation_text(self, item: Dict[str, Any]) -> str:
        """Constructs rich narrative for an item."""
        return f"{item.get('title', '')}. Category: {item.get('category', '')}. {item.get('description', '')}. Tags: {', '.join(item.get('tags', []))}."

    def retrieve_candidates(self, context: PatientContext, domain: str = "clinical_intervention", top_n: int = 50) -> List[CandidateItem]:
        """
        Executes Stage 1 Candidate Retrieval:
        Computes patient embedding and evaluates vector similarity against the domain items.
        """
        # 1. Generate Patient Tower Vector
        patient_text = self._build_patient_representation_text(context)
        patient_vector = embed_text(patient_text)

        # 2. Retrieve Items for Domain
        catalog_items = ClinicalKnowledgeUniverse.get_items_for_domain(domain)
        candidates: List[CandidateItem] = []

        for raw_item in catalog_items:
            item_id = raw_item["item_id"]
            if item_id not in self._item_embeddings_cache:
                item_text = self._build_item_representation_text(raw_item)
                self._item_embeddings_cache[item_id] = embed_text(item_text)
            
            item_vector = self._item_embeddings_cache[item_id]
            sim = _cosine_similarity(patient_vector, item_vector)

            candidate = CandidateItem(
                item_id=raw_item["item_id"],
                title=raw_item["title"],
                category=raw_item["category"],
                description=raw_item["description"],
                evidence_level=raw_item.get("evidence_level", "Level 1A"),
                contraindications=raw_item.get("contraindications", []),
                tags=raw_item.get("tags", []),
                embedding=item_vector,
                similarity_score=sim
            )
            candidates.append(candidate)

        # Sort by similarity descending
        candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        return candidates[:top_n]
