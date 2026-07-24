"""
Acute Decompensated Heart Failure (ADHF) Pseudo-WRF vs True WRF Engine
========================================================================
Differentiates Pseudo-Worsening Renal Function (successful decongestion, hemoconcentration, falling NT-proBNP)
from True WRF (persistent congestion, worsening hemodynamics, oliguria) during IV loop diuresis.
"""

from typing import Dict


class AdhfPseudoWrfEngine:
    """Differentiates Pseudo-WRF from True WRF during aggressive heart failure decongestion."""

    def differentiate_wrf_type(
        self,
        baseline_creatinine_mg_dL: float,
        current_creatinine_mg_dL: float,
        hemoconcentration_present: bool = True,  # Increase in hematocrit/total protein/albumin during diuresis
        nt_probnp_declining: bool = True,  # > 30% reduction in NT-proBNP
        persistent_congestion_signs: bool = False,  # S3 gallop, persistent peripheral edema, rising JVP
        urine_output_adequate: bool = True,  # > 0.5 mL/kg/h
    ) -> Dict[str, any]:
        creatinine_rise = current_creatinine_mg_dL - baseline_creatinine_mg_dL
        creatinine_rise_percent = (
            (creatinine_rise / baseline_creatinine_mg_dL) * 100.0 if baseline_creatinine_mg_dL > 0 else 0.0
        )

        wrf_present = creatinine_rise >= 0.3 or creatinine_rise_percent >= 25.0

        wrf_type = "NO_WRF"
        if wrf_present:
            if hemoconcentration_present and nt_probnp_declining and urine_output_adequate and not persistent_congestion_signs:
                wrf_type = "PSEUDO_WRF"
            else:
                wrf_type = "TRUE_WRF"

        diuretic_action = "CONTINUE_OR_TITRATE_IV_LOOP_DIURETICS"
        if wrf_type == "TRUE_WRF":
            diuretic_action = "HOLD_OR_REDUCE_DIURETICS_EVALUATE_PERFUSION_AND_INOTROPES"

        recommendation = "No significant worsening renal function detected; continue current heart failure management"
        if wrf_type == "PSEUDO_WRF":
            recommendation = f"BENIGN PSEUDO-WRF DETECTED (Cr rise {creatinine_rise:.2f} mg/dL, {creatinine_rise_percent:.1f}%): Serum creatinine rise is secondary to successful intravascular decongestion and hemoconcentration with falling NT-proBNP. DO NOT WITHDRAW OR REDUCE IV DIURETICS; continue aggressive decongestion until dry weight achieved"
        elif wrf_type == "TRUE_WRF":
            recommendation = f"TRUE WORSENING RENAL FUNCTION (Cr rise {creatinine_rise:.2f} mg/dL): Renal impairment accompanied by persistent congestion or low output state. Reduce/hold IV diuretics, evaluate for cardiorenal syndrome type 1, and consider inotropic support (Dobutamine / Milrinone)"

        return {
            "creatinine_rise_mg_dL": round(creatinine_rise, 2),
            "creatinine_rise_percent": round(creatinine_rise_percent, 1),
            "wrf_present": wrf_present,
            "wrf_type": wrf_type,
            "diuretic_action": diuretic_action,
            "clinical_recommendation": recommendation,
            "status": "DIFFERENTIATION_COMPLETE",
        }


# Singleton engine instance
pseudo_wrf_engine = AdhfPseudoWrfEngine()
