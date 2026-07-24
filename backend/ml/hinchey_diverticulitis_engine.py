"""
Acute Diverticulitis Hinchey Classification & Staging Engine
============================================================
Stages acute complicated diverticulitis from Stage I to Stage IV on CT abdomen
to guide IR percutaneous drainage vs emergency Hartmann's procedure / laparotomy.
"""

from typing import Dict


class HincheyDiverticulitisEngine:
    """Stages acute diverticulitis via CT-based Modified Hinchey Classification."""

    def stage_hinchey_diverticulitis(
        self,
        pericolic_abscess_present: bool = False,
        distant_pelvic_retroperitoneal_abscess: bool = False,
        purulent_peritonitis_free_air: bool = False,
        fecal_peritonitis_gross_contamination: bool = False,
    ) -> Dict[str, any]:
        stage = "UNCOMPLICATED_DIVERTICULITIS"
        surgery = False

        if fecal_peritonitis_gross_contamination:
            stage = "HINCHEY_STAGE_IV_FECAL_PERITONITIS"
            surgery = True
        elif purulent_peritonitis_free_air:
            stage = "HINCHEY_STAGE_III_PURULENT_PERITONITIS"
            surgery = True
        elif distant_pelvic_retroperitoneal_abscess:
            stage = "HINCHEY_STAGE_II_PELVIC_ABSCEESS"
        elif pericolic_abscess_present:
            stage = "HINCHEY_STAGE_I_PERICOLIC_ABSCESS"

        recommendation = "Outpatient oral antibiotics (Amoxicillin-Clavulanate / Ciprofloxacin + Metronidazole)"
        if surgery:
            recommendation = "Stat Emergency Exploratory Laparotomy & Hartmann's Resection / Primary Anastomosis with Loop Ileostomy"
        elif stage in ["HINCHEY_STAGE_I_PERICOLIC_ABSCESS", "HINCHEY_STAGE_II_PELVIC_ABSCEESS"]:
            recommendation = "CT-guided IR Percutaneous Abscess Drainage (>4cm) & IV Pip/Tazo"

        return {
            "hinchey_stage": stage,
            "emergency_surgery_indicated": surgery,
            "ir_percutaneous_drainage_indicated": stage in ["HINCHEY_STAGE_I_PERICOLIC_ABSCESS", "HINCHEY_STAGE_II_PELVIC_ABSCEESS"],
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
hinchey_engine = HincheyDiverticulitisEngine()
