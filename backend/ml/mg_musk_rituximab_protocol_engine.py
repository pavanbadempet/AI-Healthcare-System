"""
Myasthenia Gravis MuSK-Positive Anti-CD20 Rituximab Protocol Engine
====================================================================
Evaluates MuSK IgG4 antibody positive generalized Myasthenia Gravis: calculates Rituximab protocol
(375 mg/m2 weekly x 4 vs 1000 mg IV Day 1/15) and monitors CD19/CD20 B-cell depletion (< 0.05%).
"""

from typing import Dict


class MgMuskRituximabProtocolEngine:
    """Evaluates Rituximab protocol and B-cell depletion monitoring in MuSK+ MG."""

    def evaluate_musk_rituximab_protocol(
        self,
        musk_antibody_positive: bool = True,
        cd19_cd20_b_cell_percent: float = 0.0,  # < 0.05% = complete depletion
        months_since_last_rituximab_infusion: float = 6.0,
        body_surface_area_m2: float = 1.8,
        dosing_regimen_type: str = "FIXED_DOSE_1000MG",  # FIXED_DOSE_1000MG or ONCOLOGY_375MG_M2
    ) -> Dict[str, any]:
        b_cell_repleted = cd19_cd20_b_cell_percent >= 0.05 and months_since_last_rituximab_infusion >= 6.0

        rituximab_indicated = musk_antibody_positive and (months_since_last_rituximab_infusion == 0.0 or b_cell_repleted)

        dosing_summary = "1000 mg IV on Day 1 and Day 15 (2-dose cycle)"
        if dosing_regimen_type == "ONCOLOGY_375MG_M2":
            calculated_weekly_dose_mg = round(375.0 * body_surface_area_m2, 0)
            dosing_summary = f"{calculated_weekly_dose_mg} mg IV once weekly for 4 consecutive weeks"

        recommendation = "Rituximab redosing NOT indicated (CD19/CD20 B-cells depleted < 0.05%); monitor B-cell repletion Q3M"
        if rituximab_indicated:
            recommendation = f"RITUXIMAB INDICATED FOR MuSK+ MYASTHENIA GRAVIS (Complete remission rate > 70%): Administer {dosing_summary}. Pre-medicate with Methylprednisolone 100 mg IV + Acetaminophen + Diphenhydramine 30 minutes prior"

        return {
            "musk_antibody_positive": musk_antibody_positive,
            "b_cell_repleted": b_cell_repleted,
            "rituximab_indicated": rituximab_indicated,
            "recommended_regimen": dosing_summary if rituximab_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
musk_rituximab_engine = MgMuskRituximabProtocolEngine()
