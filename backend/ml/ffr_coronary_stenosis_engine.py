"""
Invasive Fractional Flow Reserve (FFR) & iFR Coronary Stenosis Engine
======================================================================
Evaluates distal coronary pressure to aortic pressure ratio (FFR <= 0.80 or iFR <= 0.89)
to determine physiological ischemia and revascularization indications.
"""

from typing import Dict, Optional


class FfrCoronaryStenosisEngine:
    """Evaluates invasive FFR and iFR measurements for coronary stenosis significance."""

    def evaluate_coronary_ischemia(
        self,
        pd_pa_hyperemic_ffr: Optional[float] = None,
        instantaneous_wave_free_ratio_ifr: Optional[float] = None,
        angiographic_stenosis_percent: float = 60.0,
    ) -> Dict[str, any]:
        hemodynamically_significant = False
        mechanism = "NON_ISCHEMIC_INTERMEDIATE_LESION"

        if pd_pa_hyperemic_ffr is not None and pd_pa_hyperemic_ffr <= 0.80:
            hemodynamically_significant = True
            mechanism = "ISCHEMIC_FFR_POSITIVE"
        elif instantaneous_wave_free_ratio_ifr is not None and instantaneous_wave_free_ratio_ifr <= 0.89:
            hemodynamically_significant = True
            mechanism = "ISCHEMIC_IFR_POSITIVE"

        recommendation = "FFR > 0.80 / iFR > 0.89: Defer PCI; manage with Optimal Medical Therapy (OMT)"
        if hemodynamically_significant:
            recommendation = "Physiological Ischemia Confirmed: Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stent (DES) indicated"

        return {
            "pd_pa_hyperemic_ffr": pd_pa_hyperemic_ffr,
            "instantaneous_wave_free_ratio_ifr": instantaneous_wave_free_ratio_ifr,
            "hemodynamically_significant_ischemia": hemodynamically_significant,
            "ischemia_mechanism": mechanism,
            "pci_revascularization_indicated": hemodynamically_significant,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ffr_coronary_engine = FfrCoronaryStenosisEngine()
