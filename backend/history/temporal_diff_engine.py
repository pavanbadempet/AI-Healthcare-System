"""Temporal Differential Engine & Visual Clinical Time Machine.

Computes semantic deltas Δ(T_1, T_2) between arbitrary clinical timepoints,
isolating added diagnoses, adjusted medication dosages, revoked allergies,
and vital sign trends for shift handoffs and medical-legal discovery.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List

from backend.history.clinical_event_store import ClinicalEventStore


def diff_patient_states(
    state_t1: Dict[str, Any],
    state_t2: Dict[str, Any],
    t1_label: str = "T1",
    t2_label: str = "T2",
) -> Dict[str, Any]:
    """Compute structural clinical difference between two projected patient states."""
    added: Dict[str, List[Any]] = {
        "conditions": [],
        "medications": [],
        "allergies": [],
        "labs": [],
    }
    modified: Dict[str, List[Any]] = {
        "conditions": [],
        "medications": [],
        "allergies": [],
    }
    resolved_or_revoked: Dict[str, List[Any]] = {
        "conditions": [],
        "medications": [],
        "allergies": [],
    }
    narrative: List[str] = []

    # 1. Compare Conditions
    c1 = state_t1.get("conditions", {})
    c2 = state_t2.get("conditions", {})

    for code, cond2 in c2.items():
        if code not in c1:
            added["conditions"].append(cond2)
            narrative.append(f"Condition diagnosed: {cond2.get('name')} ({code}) with severity {cond2.get('severity')}")
        else:
            cond1 = c1[code]
            if cond1.get("status") != cond2.get("status") or cond1.get("severity") != cond2.get("severity"):
                mod = {
                    "code": code,
                    "name": cond2.get("name"),
                    "from_status": cond1.get("status"),
                    "to_status": cond2.get("status"),
                    "from_severity": cond1.get("severity"),
                    "to_severity": cond2.get("severity"),
                }
                modified["conditions"].append(mod)
                if cond2.get("status") == "RESOLVED":
                    resolved_or_revoked["conditions"].append(cond2)
                    narrative.append(f"Condition resolved: {cond2.get('name')} ({code})")
                else:
                    narrative.append(f"Condition updated: {cond2.get('name')} ({code}) severity {cond1.get('severity')} -> {cond2.get('severity')}")

    # 2. Compare Medications
    m1 = state_t1.get("medications", {})
    m2 = state_t2.get("medications", {})

    for med_id, med2 in m2.items():
        if med_id not in m1:
            added["medications"].append(med2)
            narrative.append(f"Medication started: {med2.get('name')} {med2.get('dose')}{med2.get('unit')} {med2.get('frequency')}")
        else:
            med1 = m1[med_id]
            dose_changed = med1.get("dose") != med2.get("dose")
            status_changed = med1.get("status") != med2.get("status")

            if dose_changed or status_changed:
                mod = {
                    "medication_id": med_id,
                    "name": med2.get("name"),
                    "from_dose": med1.get("dose"),
                    "to_dose": med2.get("dose"),
                    "unit": med2.get("unit"),
                    "from_status": med1.get("status"),
                    "to_status": med2.get("status"),
                }
                modified["medications"].append(mod)
                if dose_changed:
                    narrative.append(f"Dose adjusted: {med2.get('name')} {med1.get('dose')}{med1.get('unit')} -> {med2.get('dose')}{med2.get('unit')}")
                if status_changed and med2.get("status") == "DISCONTINUED":
                    resolved_or_revoked["medications"].append(med2)
                    narrative.append(f"Medication discontinued: {med2.get('name')}")

    # 3. Compare Allergies
    a1 = state_t1.get("allergies", {})
    a2 = state_t2.get("allergies", {})

    for allergen, alg2 in a2.items():
        if allergen not in a1:
            added["allergies"].append(alg2)
            narrative.append(f"Allergy flagged: {allergen} (Reaction: {alg2.get('reaction')})")
        else:
            alg1 = a1[allergen]
            if alg1.get("status") != alg2.get("status"):
                modified["allergies"].append({
                    "allergen": allergen,
                    "from_status": alg1.get("status"),
                    "to_status": alg2.get("status"),
                })
                if alg2.get("status") == "REVOKED":
                    resolved_or_revoked["allergies"].append(alg2)
                    narrative.append(f"Allergy revoked: {allergen}")

    # 4. Compare Labs
    l1 = state_t1.get("labs", {})
    l2 = state_t2.get("labs", {})
    for test_name, lab2 in l2.items():
        if test_name not in l1:
            added["labs"].append(lab2)
            narrative.append(f"New lab resulted: {test_name} = {lab2.get('value')} {lab2.get('unit')} ({lab2.get('flag')})")
        elif l1[test_name].get("value") != lab2.get("value"):
            narrative.append(f"Lab updated: {test_name} changed from {l1[test_name].get('value')} to {lab2.get('value')} {lab2.get('unit')}")

    # 5. Vitals Delta
    v1_count = len(state_t1.get("vitals", []))
    v2 = state_t2.get("vitals", [])
    new_vitals = v2[v1_count:]
    if new_vitals:
        narrative.append(f"{len(new_vitals)} new vital sign observations recorded")

    return {
        "t1_label": t1_label,
        "t2_label": t2_label,
        "added": added,
        "modified": modified,
        "resolved_or_revoked": resolved_or_revoked,
        "new_vitals_count": len(new_vitals),
        "new_vitals": new_vitals,
        "clinical_narrative": narrative,
        "total_structural_changes": (
            len(added["conditions"])
            + len(added["medications"])
            + len(added["allergies"])
            + len(added["labs"])
            + len(modified["conditions"])
            + len(modified["medications"])
            + len(modified["allergies"])
        ),
    }


class TemporalDiffEngine:
    """Orchestrator for comparing patient timelines and computing shift handoffs."""

    def __init__(self, event_store: ClinicalEventStore) -> None:
        self.event_store = event_store

    def diff_patient_at_times(
        self,
        patient_id: str,
        t1: datetime.datetime,
        t2: datetime.datetime,
        by_valid_time: bool = False,
    ) -> Dict[str, Any]:
        """Compute state delta between two chronological milestones."""
        state_t1 = self.event_store.project_patient_chart(
            patient_id=patient_id,
            as_of_time=t1,
            by_valid_time=by_valid_time,
        )
        state_t2 = self.event_store.project_patient_chart(
            patient_id=patient_id,
            as_of_time=t2,
            by_valid_time=by_valid_time,
        )

        return diff_patient_states(
            state_t1=state_t1,
            state_t2=state_t2,
            t1_label=t1.isoformat(),
            t2_label=t2.isoformat(),
        )
