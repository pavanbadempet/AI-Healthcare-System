"""
Idiopathic Intracranial Hypertension (IIH) Venous Sinus Stenting Engine
========================================================================
Evaluates catheter venography trans-stenotic peak pressure gradient (>= 8-10 mmHg),
MRV transverse sinus stenosis, LP opening pressure, and papilledema to select
endovascular self-expanding venous sinus stenting.
"""

from typing import Dict


class IihVenousSinusStentingEngine:
    """Evaluates trans-stenotic pressure gradient and venous sinus stenting candidacy in IIH."""

    def evaluate_stenting_candidacy(
        self,
        trans_stenotic_peak_pressure_gradient_mmHg: float,  # Must be >= 8.0-10.0 mmHg
        transverse_sinus_stenosis_on_mrv: bool,
        lp_opening_pressure_mm_h2o: float,
        refractory_to_acetazolamide: bool = True,
        frisen_papilledema_grade: int = 3,
    ) -> Dict[str, any]:
        significant_gradient = trans_stenotic_peak_pressure_gradient_mmHg >= 8.0
        stenting_indicated = (
            transverse_sinus_stenosis_on_mrv
            and significant_gradient
            and refractory_to_acetazolamide
            and lp_opening_pressure_mm_h2o >= 250.0
        )

        stent_type = "NOT_INDICATED"
        if stenting_indicated:
            stent_type = "SELF_EXPANDING_NITINOL_VENOUS_STENT_TRANSVERSE_SINUS"

        recommendation = "Trans-stenotic gradient < 8 mmHg or conservative management adequate; stenting not indicated"
        if stenting_indicated:
            recommendation = f"Candidate for Endovascular Venous Sinus Stenting (Peak Gradient {trans_stenotic_peak_pressure_gradient_mmHg} mmHg >= 8 mmHg): Place self-expanding nitinol stent across dominant transverse-sigmoid sinus stenosis + dual antiplatelet therapy (Aspirin + Clopidogrel 3 months)"

        return {
            "trans_stenotic_gradient_mmHg": trans_stenotic_peak_pressure_gradient_mmHg,
            "significant_gradient": significant_gradient,
            "stenting_indicated": stenting_indicated,
            "recommended_stent_type": stent_type,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
iih_stenting_engine = IihVenousSinusStentingEngine()
