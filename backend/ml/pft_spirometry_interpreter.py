"""
Pulmonary Function Test (PFT) Spirometry Interpreter
=====================================================
Evaluates FEV1/FVC ratios and Total Lung Capacity (TLC) to classify Obstructive
(COPD, Asthma) vs Restrictive lung disease patterns.
"""

from typing import Dict, Optional


class PftSpirometryInterpreter:
    """Interprets spirometry and lung volume test results."""

    def interpret_spirometry(
        self,
        fev1_liters: float,
        fvc_liters: float,
        fev1_percent_predicted: float,
        tlc_percent_predicted: Optional[float] = None,
    ) -> Dict[str, any]:
        fev1_fvc_ratio = round((fev1_liters / max(fvc_liters, 0.1)) * 100, 1)

        pattern = "NORMAL_SPIROMETRY"
        severity = "NORMAL"

        if fev1_fvc_ratio < 70.0:
            pattern = "OBSTRUCTIVE_DEFECT"
            if fev1_percent_predicted < 35.0:
                severity = "VERY_SEVERE"
            elif fev1_percent_predicted < 50.0:
                severity = "SEVERE"
            elif fev1_percent_predicted < 80.0:
                severity = "MODERATE"
            else:
                severity = "MILD"
        elif tlc_percent_predicted and tlc_percent_predicted < 80.0:
            pattern = "RESTRICTIVE_DEFECT"
            severity = "MODERATE"

        return {
            "fev1_fvc_ratio_percent": fev1_fvc_ratio,
            "fev1_percent_predicted": fev1_percent_predicted,
            "spirometry_pattern": pattern,
            "defect_severity": severity,
            "status": "INTERPRETATION_COMPLETE",
        }


# Singleton interpreter instance
pft_interpreter = PftSpirometryInterpreter()
