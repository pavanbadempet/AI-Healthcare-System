"""
Amyotrophic Lateral Sclerosis (ALS) Gold Coast Diagnostic Criteria Engine
========================================================================
Evaluates 2020 Gold Coast Criteria for ALS diagnosis: Progressive motor impairment in >= 1 body region
with combined UMN and LMN signs, excluding mimic syndromes to initiate Riluzole + Edaravone + Tofersen.
"""

from typing import Dict


class AlsGoldCoastCriteriaEngine:
    """Evaluates 2020 Gold Coast Criteria for Amyotrophic Lateral Sclerosis (ALS)."""

    def evaluate_gold_coast_als(
        self,
        progressive_motor_impairment: bool,
        bulbar_umn_lmn_signs: bool = False,
        cervical_umn_lmn_signs: bool = False,
        thoracic_umn_lmn_signs: bool = False,
        lumbosacral_umn_lmn_signs: bool = False,
        emg_denervation_fasciculations_present: bool = True,
        sod1_mutation_present: bool = False,
        mimic_syndrome_excluded: bool = True,
    ) -> Dict[str, any]:
        regions_count = sum([bulbar_umn_lmn_signs, cervical_umn_lmn_signs, thoracic_umn_lmn_signs, lumbosacral_umn_lmn_signs])

        gold_coast_met = progressive_motor_impairment and mimic_syndrome_excluded and (regions_count >= 1 or emg_denervation_fasciculations_present)

        pharmacotherapy = "OBSERVATION_OR_RE_EVALUATE"
        if gold_coast_met:
            if sod1_mutation_present:
                pharmacotherapy = "RILUZOLE_50MG_BID_PLUS_EDARAVONE_PLUS_TOFERSEN_ANTISENSE_OLIGONUCLEOTIDE"
            else:
                pharmacotherapy = "RILUZOLE_50MG_BID_PLUS_EDARAVONE_IV_OR_ORAL"

        recommendation = "Gold Coast ALS Criteria NOT met; evaluate motor neuron mimics (e.g., Multifocal Motor Neuropathy, Spinal Muscular Atrophy)"
        if gold_coast_met:
            recommendation = f"Confirmed ALS (Gold Coast Criteria MET across {regions_count} regions): Initiate {pharmacotherapy}; establish baseline ALSFRS-R & FVC parameters"

        return {
            "progressive_motor_impairment": progressive_motor_impairment,
            "involved_body_regions_count": regions_count,
            "gold_coast_criteria_met": gold_coast_met,
            "recommended_pharmacotherapy": pharmacotherapy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
als_gold_coast_engine = AlsGoldCoastCriteriaEngine()
