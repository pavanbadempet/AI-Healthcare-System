"""Clinical Record Branching & Counterfactual Simulation Engine.

Enables clinicians to fork live patient charts into isolated Copy-on-Write (CoW)
simulation branches (e.g. testing Regimen A vs Regimen B in oncology or ICU care),
simulate hypothetical interventions, and merge approved treatment trajectories
back to the canonical patient chart using a 3-way merge conflict resolver.
"""

from __future__ import annotations

import copy
import datetime
import uuid
from typing import Any, Dict, List, Optional

from backend.history.clinical_event_store import (
    ClinicalDomainEvent,
    ClinicalEventStore,
    EventType,
)


class MergeConflict:
    """Represents a concurrent mutation conflict between trunk and simulation branch."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        trunk_value: Any,
        branch_value: Any,
        conflict_type: str,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.trunk_value = trunk_value
        self.branch_value = branch_value
        self.conflict_type = conflict_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "trunk_value": self.trunk_value,
            "branch_value": self.branch_value,
            "conflict_type": self.conflict_type,
        }


class BranchMetadata:
    """Metadata and event sequence for an isolated patient simulation workspace."""

    def __init__(
        self,
        branch_id: str,
        patient_id: str,
        branch_name: str,
        author_id: str,
        author_name: str,
        purpose: str,
        base_snapshot: Dict[str, Any],
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.branch_id = branch_id
        self.patient_id = patient_id
        self.branch_name = branch_name
        self.author_id = author_id
        self.author_name = author_name
        self.purpose = purpose
        self.base_snapshot = base_snapshot
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.branch_events: List[ClinicalDomainEvent] = []
        self.status = "ACTIVE"  # ACTIVE, MERGED, ABANDONED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "patient_id": self.patient_id,
            "branch_name": self.branch_name,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "branch_events_count": len(self.branch_events),
        }


class ChartBranchEngine:
    """Orchestrates patient chart branching, hypothetical simulation, and 3-way merging."""

    def __init__(self, event_store: ClinicalEventStore) -> None:
        self.event_store = event_store
        self._branches: Dict[str, BranchMetadata] = {}  # branch_id -> branch

    def create_branch(
        self,
        patient_id: str,
        branch_name: str,
        author_id: str,
        author_name: str,
        purpose: str,
    ) -> BranchMetadata:
        """Fork the current canonical patient chart into an isolated simulation branch."""
        bid = str(uuid.uuid4())
        # Copy-on-Write: take immutable projection snapshot of canonical chart
        base_snapshot = self.event_store.project_patient_chart(patient_id=patient_id)

        meta = BranchMetadata(
            branch_id=bid,
            patient_id=patient_id,
            branch_name=branch_name,
            author_id=author_id,
            author_name=author_name,
            purpose=purpose,
            base_snapshot=copy.deepcopy(base_snapshot),
        )
        self._branches[bid] = meta
        return meta

    def mutate_branch(
        self,
        branch_id: str,
        event_type: EventType | str,
        payload: Dict[str, Any],
        valid_time: Optional[datetime.datetime] = None,
    ) -> ClinicalDomainEvent:
        """Append a simulated clinical decision within the isolated branch workspace."""
        branch = self._branches.get(branch_id)
        if not branch:
            raise KeyError(f"Simulation branch '{branch_id}' not found")
        if branch.status != "ACTIVE":
            raise ValueError(f"Cannot mutate branch with status '{branch.status}'")

        v_time = valid_time or datetime.datetime.now(datetime.timezone.utc)
        now = datetime.datetime.now(datetime.timezone.utc)

        seq = len(branch.branch_events) + 1
        prev_hash = branch.branch_events[-1].event_hash if branch.branch_events else (branch.base_snapshot.get("last_event_hash") or "BASE")

        event = ClinicalDomainEvent(
            event_id=str(uuid.uuid4()),
            patient_id=branch.patient_id,
            event_type=event_type,
            timestamp=now,
            valid_time=v_time,
            node_id=f"branch_{branch_id[:8]}",
            vector_clock={f"sim_{branch_id[:8]}": seq},
            causal_sequence=seq,
            payload=payload,
            intent_id=f"SIMULATION_{branch.branch_name}",
            prev_hash=prev_hash,
        )

        branch.branch_events.append(event)
        return event

    def get_branch_state(self, branch_id: str) -> Dict[str, Any]:
        """Project the current hypothetical chart state for the simulation branch."""
        branch = self._branches.get(branch_id)
        if not branch:
            raise KeyError(f"Simulation branch '{branch_id}' not found")

        # Start from base snapshot and fold branch events
        state = copy.deepcopy(branch.base_snapshot)

        for ev in branch.branch_events:
            ev_type = ev.event_type
            p = ev.payload

            if ev_type == EventType.MEDICATION_PRESCRIBED:
                med_id = p.get("medication_id", p.get("name", str(uuid.uuid4())))
                state["medications"][med_id] = {
                    "medication_id": med_id,
                    "name": p.get("name", "Unknown"),
                    "dose": p.get("dose"),
                    "unit": p.get("unit", "mg"),
                    "status": "ACTIVE",
                    "route": p.get("route", "ORAL"),
                    "prescribed_at": ev.valid_time.isoformat(),
                    "adjustments": [],
                }
            elif ev_type == EventType.DOSAGE_ADJUSTED:
                med_id = p.get("medication_id", p.get("name"))
                if med_id and med_id in state["medications"]:
                    med = state["medications"][med_id]
                    med["adjustments"].append({
                        "previous_dose": med["dose"],
                        "new_dose": p.get("new_dose"),
                        "adjusted_at": ev.valid_time.isoformat(),
                        "reason": p.get("reason", "Hypothetical Simulation Adjustment"),
                    })
                    med["dose"] = p.get("new_dose")
            elif ev_type == EventType.MEDICATION_DISCONTINUED:
                med_id = p.get("medication_id", p.get("name"))
                if med_id and med_id in state["medications"]:
                    state["medications"][med_id]["status"] = "DISCONTINUED"
                    state["medications"][med_id]["discontinue_reason"] = p.get("reason", "Simulated Discontinuation")
            elif ev_type == EventType.CONDITION_DIAGNOSED:
                code = p.get("code", str(uuid.uuid4()))
                state["conditions"][code] = {
                    "code": code,
                    "name": p.get("name", "Hypothetical Condition"),
                    "severity": p.get("severity", "MODERATE"),
                    "status": "ACTIVE",
                }

        state["branch_id"] = branch_id
        state["branch_name"] = branch.branch_name
        state["simulated_event_count"] = len(branch.branch_events)
        return state

    def three_way_merge(
        self,
        branch_id: str,
        merging_clinician_id: str,
        merging_clinician_name: str,
        allow_conflict_override: bool = False,
    ) -> Dict[str, Any]:
        """Perform 3-way merge between base ancestor, current live trunk, and branch."""
        branch = self._branches.get(branch_id)
        if not branch:
            raise KeyError(f"Simulation branch '{branch_id}' not found")
        if branch.status != "ACTIVE":
            raise ValueError(f"Cannot merge branch in state '{branch.status}'")

        patient_id = branch.patient_id
        base_state = branch.base_snapshot
        trunk_state = self.event_store.project_patient_chart(patient_id=patient_id)
        branch_state = self.get_branch_state(branch_id)

        conflicts: List[MergeConflict] = []

        # Compare medications across base, trunk, branch
        base_meds = base_state.get("medications", {})
        trunk_meds = trunk_state.get("medications", {})
        branch_meds = branch_state.get("medications", {})

        all_med_keys = set(base_meds.keys()).union(trunk_meds.keys()).union(branch_meds.keys())

        for med_k in all_med_keys:
            b_val = base_meds.get(med_k)
            t_val = trunk_meds.get(med_k)
            br_val = branch_meds.get(med_k)

            # Check if both trunk and branch modified the medication differently
            trunk_modified = (b_val != t_val)
            branch_modified = (b_val != br_val)

            if trunk_modified and branch_modified:
                # Concurrent mutation conflict
                t_dose = t_val.get("dose") if t_val else None
                br_dose = br_val.get("dose") if br_val else None
                t_status = t_val.get("status") if t_val else None
                br_status = br_val.get("status") if br_val else None

                if t_dose != br_dose or t_status != br_status:
                    conflicts.append(
                        MergeConflict(
                            entity_type="medication",
                            entity_id=med_k,
                            trunk_value={"dose": t_dose, "status": t_status},
                            branch_value={"dose": br_dose, "status": br_status},
                            conflict_type="CONCURRENT_MEDICATION_MODIFICATION",
                        )
                    )

        if conflicts and not allow_conflict_override:
            return {
                "success": False,
                "status": "MERGE_CONFLICT",
                "branch_id": branch_id,
                "conflicts": [c.to_dict() for c in conflicts],
                "applied_events_count": 0,
            }

        # Apply non-conflicting branch events to canonical trunk event store
        applied_count = 0
        for b_ev in branch.branch_events:
            payload_with_attribution = dict(b_ev.payload)
            payload_with_attribution["_merged_from_branch"] = branch.branch_name
            payload_with_attribution["_merging_clinician"] = {
                "id": merging_clinician_id,
                "name": merging_clinician_name,
            }

            self.event_store.append(
                patient_id=patient_id,
                event_type=b_ev.event_type,
                payload=payload_with_attribution,
                valid_time=b_ev.valid_time,
                node_id=f"merge_{merging_clinician_id}",
                intent_id=f"MERGE_{branch.branch_name}",
            )
            applied_count += 1

        branch.status = "MERGED"
        final_chart = self.event_store.project_patient_chart(patient_id=patient_id)

        return {
            "success": True,
            "status": "MERGED_TO_TRUNK",
            "branch_id": branch_id,
            "patient_id": patient_id,
            "applied_events_count": applied_count,
            "conflicts_overridden": len(conflicts),
            "merged_chart": final_chart,
        }

    def list_patient_branches(self, patient_id: str) -> List[BranchMetadata]:
        """List all simulation branches created for a given patient."""
        return [
            b for b in self._branches.values()
            if b.patient_id == patient_id
        ]

    def clear(self) -> None:
        """Reset internal branches (for testing)."""
        self._branches.clear()
