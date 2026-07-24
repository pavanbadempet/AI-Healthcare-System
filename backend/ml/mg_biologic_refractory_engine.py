"""
Myasthenia Gravis Biologic Therapy (Rituximab / Inebilizumab / Satralizumab) Engine
======================================================================================
Evaluates anti-MuSK antibody positive or double-seronegative refractory generalized MG.
Recommends B-cell depleting agents (Rituximab anti-CD20, Inebilizumab anti-CD19) or IL-6 receptor blocker (Satralizumab)
which yield high complete stable remission rates in MuSK-MG (where Pyridostigmine has poor efficacy).
"""

from typing import Dict


class MgBiologicRefractoryEngine:
    """Evaluates targeted biologic agents for anti-MuSK+ and refractory generalized MG."""

    def evaluate_biologic_candidate(
        self,
        musk_antibody_positive: bool = True,
        achr_antibody_positive: bool = False,
        refractory_to_steroids_or_isrs: bool = True,
        pyridostigmine_intolerance_or_poor_response: bool = True,
    ) -> Dict[str, any]:
        biologic_indicated = musk_antibody_positive or (
            not achr_antibody_positive and refractory_to_steroids_or_isrs
        )

        first_line_biologic = "NONE"
        if musk_antibody_positive:
            first_line_biologic = "RITUXIMAB_ANTI_CD20_1000MG_IV_TWO_DOSES_TWO_WEEKS_APART"
        elif refractory_to_steroids_or_isrs:
            first_line_biologic = "INEBILIZUMAB_ANTI_CD19_OR_SATRALIZUMAB_IL6R_ANTAGONIST"

        recommendation = "Targeted B-cell/IL-6 biologic therapy not currently indicated; manage with AChR-directed therapies (Pyridostigmine, steroids, FcRn antagonists)"
        if biologic_indicated:
            recommendation = f"RECOMMENDED BIOLOGIC THERAPY ({first_line_biologic}): Anti-MuSK MG responds exceptionally to B-cell depletion with long-lasting remission; taper Pyridostigmine (often ineffective/poorly tolerated in MuSK-MG) and baseline immunosuppressants as response develops"

        return {
            "musk_antibody_positive": musk_antibody_positive,
            "biologic_indicated": biologic_indicated,
            "recommended_biologic": first_line_biologic,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_biologic_engine = MgBiologicRefractoryEngine()
