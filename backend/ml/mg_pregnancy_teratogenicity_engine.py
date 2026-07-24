"""
Myasthenia Gravis Pregnancy & Teratogenicity Safety Engine
===========================================================
Evaluates safety of immunomodulatory medications during pregnancy / preconception planning.
Identifies safe agents (Pyridostigmine, Prednisone, Azathioprine - low risk, IVIG, PLEX)
vs strictly contraindicated teratogenic drugs (Mycophenolate mofetil MMF, Methotrexate, Cyclophosphamide).
"""

from typing import Dict


class MgPregnancyTeratogenicityEngine:
    """Evaluates drug safety and teratogenicity risk in pregnant Myasthenia Gravis patients."""

    def evaluate_pregnancy_drug_safety(
        self,
        current_medications: list[str],
        patient_currently_pregnant: bool = True,
    ) -> Dict[str, any]:
        strictly_contraindicated = []
        safe_medications = []
        cautious_medications = []

        med_map = {
            "MYCOPHENOLATE": "TERATOGENIC_CATEGORY_X_MYCOPHENOLATE_MOFETIL",
            "MMF": "TERATOGENIC_CATEGORY_X_MYCOPHENOLATE_MOFETIL",
            "METHOTREXATE": "TERATOGENIC_CATEGORY_X_METHOTREXATE",
            "CYCLOPHOSPHAMIDE": "TERATOGENIC_CATEGORY_D_CYCLOPHOSPHAMIDE",
            "PYRIDOSTIGMINE": "SAFE_ORAL_CHOLINESTERASE_INHIBITOR",
            "PREDNISONE": "SAFE_CORTICOSTEROID_INACTIVATED_BY_PLACENTAL_11BETA_HSD2",
            "AZATHIOPRINE": "SAFE_INTRACELLULAR_METABOLITE_PROTECTED",
            "IVIG": "SAFE_INTRAVENOUS_IMMUNOGLOBULIN",
            "PLEX": "SAFE_PLASMA_EXCHANGE",
        }

        for med in current_medications:
            med_upper = med.upper().strip()
            found = False
            for key, val in med_map.items():
                if key in med_upper:
                    found = True
                    if "TERATOGENIC" in val:
                        strictly_contraindicated.append(med_upper)
                    else:
                        safe_medications.append(med_upper)
                    break
            if not found:
                cautious_medications.append(med_upper)

        has_teratogen = len(strictly_contraindicated) > 0

        action_required = "CONTINUE_SAFE_MG_THERAPY"
        if has_teratogen:
            action_required = "IMMEDIATELY_DISCONTINUE_TERATOGENIC_DRUG_AND_SWITCH_TO_PREDNISONE_OR_AZATHIOPRINE"

        recommendation = f"Current MG regimen is safe during pregnancy ({', '.join(safe_medications)}); continue oral Pyridostigmine + Prednisone as needed"
        if has_teratogen:
            recommendation = f"CRITICAL CONTRAINDICATION IN PREGNANCY: Discontinue teratogenic agent(s) ({', '.join(strictly_contraindicated)}) immediately! Switch to oral Prednisone, Azathioprine, or IVIG/PLEX to avoid spontaneous abortion and severe congenital anomalies"

        return {
            "has_teratogenic_medication": has_teratogen,
            "strictly_contraindicated_drugs": strictly_contraindicated,
            "safe_drugs": safe_medications,
            "action_required": action_required,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_pregnancy_engine = MgPregnancyTeratogenicityEngine()
