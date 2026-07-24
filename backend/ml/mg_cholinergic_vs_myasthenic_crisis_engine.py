"""
Myasthenia Gravis Cholinergic vs Myasthenic Crisis Differential Engine
========================================================================
Differentiates Cholinergic Crisis (excess muscarinic SLUDGE symptoms + high-dose Pyridostigmine > 480 mg/day)
from Myasthenic Crisis (under-dosed / infection-triggered neuromuscular failure) to guide Pyridostigmine hold vs PLEX/IVIG.
"""

from typing import Dict


class MgCholinergicVsMyasthenicCrisisEngine:
    """Differentiates Cholinergic Crisis from Myasthenic Crisis in acute weakness."""

    def differentiate_crisis(
        self,
        daily_pyridostigmine_dose_mg: float,  # > 480 mg/day increases cholinergic crisis risk
        sludge_muscarinic_symptoms_present: bool = False,  # Salivation, Lacrimation, Urination, Diarrhea, GI cramps, Emesis
        miosis_pinpoint_pupils: bool = False,
        muscle_fasciculations_present: bool = False,
        fever_or_active_infection_present: bool = False,
        recent_corticosteroid_initiation: bool = False,
    ) -> Dict[str, any]:
        cholinergic_features = sum([
            sludge_muscarinic_symptoms_present,
            miosis_pinpoint_pupils,
            muscle_fasciculations_present,
        ])

        crisis_type = "MYASTHENIC_CRISIS"

        if daily_pyridostigmine_dose_mg > 480.0 and cholinergic_features >= 2:
            crisis_type = "CHOLINERGIC_CRISIS"

        pyridostigmine_action = "CONTINUE_OR_INCREASE_PYRIDOSTIGMINE"
        if crisis_type == "CHOLINERGIC_CRISIS":
            pyridostigmine_action = "TEMPORARILY_HOLD_PYRIDOSTIGMINE_AND_GIVE_ATROPINE"

        recommendation = "MYASTHENIC CRISIS (Under-dosed / Triggered by infection or steroids): Continue Pyridostigmine; initiate emergency Plasma Exchange (PLEX 5-6 sessions) or High-Dose IVIG (2 g/kg). Intubate if FVC < 15 mL/kg"
        if crisis_type == "CHOLINERGIC_CRISIS":
            recommendation = f"CRITICAL CHOLINERGIC CRISIS (Over-dosed Pyridostigmine {daily_pyridostigmine_dose_mg} mg/day + SLUDGE symptoms): TEMPORARILY HOLD ALL PYRIDOSTIGMINE; administer IV Atropine (0.5 - 1.0 mg) to counter muscarinic excess and secure endotracheal airway"

        return {
            "daily_pyridostigmine_dose_mg": daily_pyridostigmine_dose_mg,
            "crisis_type": crisis_type,
            "pyridostigmine_action": pyridostigmine_action,
            "clinical_recommendation": recommendation,
            "status": "DIFFERENTIATION_COMPLETE",
        }


# Singleton engine instance
crisis_diff_engine = MgCholinergicVsMyasthenicCrisisEngine()
