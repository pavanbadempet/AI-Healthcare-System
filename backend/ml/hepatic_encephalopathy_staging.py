"""
Hepatic Encephalopathy West Haven Staging Engine
=================================================
Stages hepatic encephalopathy severity (Grade 1 to Grade 4) and evaluates lactulose/rifaximin dosing protocols.
"""

from typing import Dict


class HepaticEncephalopathyStagingEngine:
    """Stages hepatic encephalopathy severity using West Haven Criteria."""

    def stage_hepatic_encephalopathy(
        self,
        asterixis_present: bool,
        disoriented_to_time_place: bool,
        somnolent_or_stuporous: bool,
        comatose: bool,
        serum_ammonia_umol_L: float,
    ) -> Dict[str, any]:
        grade = "GRADE_0_SUBCLINICAL"
        action = "Monitor serum ammonia & clinical mental status"

        if comatose:
            grade = "GRADE_4_COMA"
            action = "ICU admission, intubation for airway protection, & stat Lactulose/Rifaximin via NGT"
        elif somnolent_or_stuporous:
            grade = "GRADE_3_SEVERE"
            action = "Stat Lactulose 30mL Q2H until 2-3 soft stools/day + Rifaximin 550mg BID"
        elif disoriented_to_time_place or asterixis_present:
            grade = "GRADE_2_MODERATE"
            action = "Titrate Lactulose 30mL TID to maintain 2-3 soft bowel movements/day"
        elif serum_ammonia_umol_L > 80.0:
            grade = "GRADE_1_MILD"
            action = "Initiate outpatient Lactulose 15-30mL BID"

        return {
            "west_haven_grade": grade,
            "serum_ammonia": serum_ammonia_umol_L,
            "asterixis_flapping_tremor": asterixis_present,
            "pharmacotherapy_recommendation": action,
            "requires_icu_intubation": comatose,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
hepatic_encephalopathy_engine = HepaticEncephalopathyStagingEngine()
