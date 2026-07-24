"""
Pancreatic Pseudocyst & Walled-Off Necrosis (WON) EUS Drainage Engine
======================================================================
Evaluates fluid collection diameter (>= 6 cm), wall maturity (> 4 weeks),
solid necrotic debris percentage, and luminal proximity on EUS/CT to direct
Lumen-Apposing Metal Stent (LAMS) cystogastrostomy vs direct endoscopic necrosectomy (DEN).
"""

from typing import Dict


class PancreaticPseudocystDrainageEngine:
    """Evaluates pancreatic fluid collections (PFC) for EUS-guided LAMS drainage."""

    def evaluate_pfc_drainage_eligibility(
        self,
        collection_max_diameter_cm: float,
        encapsulation_duration_weeks: float,
        necrotic_debris_percent: float = 0.0,
        symptomatic_gastric_outlet_obstruction: bool = True,
        distance_to_gastric_wall_mm: float = 5.0,
    ) -> Dict[str, any]:
        matured = encapsulation_duration_weeks >= 4.0
        large_enough = collection_max_diameter_cm >= 6.0
        close_proximity = distance_to_gastric_wall_mm <= 10.0

        drainage_indicated = symptomatic_gastric_outlet_obstruction and matured and large_enough and close_proximity

        pfc_type = "PANCREATIC_PSEUDOCYST"
        drainage_modality = "OBSERVATION"

        if drainage_indicated:
            if necrotic_debris_percent >= 15.0:
                pfc_type = "WALLED_OFF_NECROSIS_WON"
                drainage_modality = "EUS_LAMS_CYSTOGASTROSTOMY_WITH_DIRECT_ENDOSCOPIC_NECROSECTOMY"
            else:
                pfc_type = "MATURE_PANCREATIC_PSEUDOCYST"
                drainage_modality = "EUS_GUIDED_LAMS_CYSTOGASTROSTOMY"

        recommendation = "Observe PFC; continue clinical monitoring and repeat CT/MRI in 4-6 weeks to assess encapsulation maturity"
        if drainage_indicated:
            if pfc_type == "WALLED_OFF_NECROSIS_WON":
                recommendation = f"Walled-Off Necrosis (WON with {necrotic_debris_percent}% debris): Perform EUS-guided LAMS (15x10mm or 20x10mm electrocautery-enhanced stent) followed by Direct Endoscopic Necrosectomy (DEN) sessions"
            else:
                recommendation = "Mature Pancreatic Pseudocyst (FE-1 >= 6cm): Perform EUS-guided LAMS cystogastrostomy or plastic pigtail stent placement"

        return {
            "pfc_max_diameter_cm": collection_max_diameter_cm,
            "encapsulation_weeks": encapsulation_duration_weeks,
            "necrotic_debris_percent": necrotic_debris_percent,
            "pfc_type": pfc_type,
            "drainage_indicated": drainage_indicated,
            "recommended_drainage_modality": drainage_modality,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
pseudocyst_engine = PancreaticPseudocystDrainageEngine()
