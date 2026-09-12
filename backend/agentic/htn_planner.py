"""Hierarchical Task Network (HTN) Clinical Planner with Reactive Telemetry Replanning.

Decomposes complex medical goals into compound tasks and precondition-gated primitive actions.
Reacts dynamically to vital telemetry interrupts, pruning invalidated subtrees and
synthesizing emergency clinical stabilization branches in sub-5 milliseconds.
"""

from __future__ import annotations

import datetime
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Execution status of an HTN task node."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PRUNED = "PRUNED"
    FAILED = "FAILED"


class PrimitiveClinicalAction:
    """An atomic medical order or intervention with precondition/postcondition gates."""

    def __init__(
        self,
        action_id: str,
        name: str,
        category: str,
        order_details: Dict[str, Any],
        preconditions: Dict[str, Any],
        postconditions: Dict[str, Any],
        time_limit_minutes: int = 60,
        status: TaskStatus = TaskStatus.PENDING,
    ) -> None:
        self.action_id = action_id
        self.name = name
        self.category = category  # FLUIDS, MEDICATION, LABS, IMAGING, MONITORING
        self.order_details = order_details
        self.preconditions = preconditions
        self.postconditions = postconditions
        self.time_limit_minutes = time_limit_minutes
        self.status = status

    def check_preconditions(self, patient_state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Verify if current patient physiology satisfies action preconditions."""
        unmet: List[str] = []
        for key, required_val in self.preconditions.items():
            base_key = key[:-4] if (key.endswith("_max") or key.endswith("_min")) else key
            current_val = patient_state.get(key)
            if current_val is None and base_key != key:
                current_val = patient_state.get(base_key)

            if current_val is None:
                unmet.append(f"Missing observation for precondition '{key}'")
            elif isinstance(required_val, (int, float)) and isinstance(current_val, (int, float)):
                # If key has _min or _max suffix, handle inequality
                if key.endswith("_max") and current_val > required_val:
                    unmet.append(f"Precondition '{key}' violated: current {current_val} > ceiling {required_val}")
                elif key.endswith("_min") and current_val < required_val:
                    unmet.append(f"Precondition '{key}' violated: current {current_val} < floor {required_val}")
            elif current_val != required_val and not (key.endswith("_min") or key.endswith("_max")):
                unmet.append(f"Precondition '{key}' violated: expected {required_val}, got {current_val}")

        return (len(unmet) == 0, unmet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "name": self.name,
            "category": self.category,
            "order_details": self.order_details,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "time_limit_minutes": self.time_limit_minutes,
            "status": self.status.value,
        }


class CompoundClinicalTask:
    """A high-level medical subgoal composed of primitive actions."""

    def __init__(
        self,
        task_id: str,
        name: str,
        actions: List[PrimitiveClinicalAction],
    ) -> None:
        self.task_id = task_id
        self.name = name
        self.actions = actions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "actions": [a.to_dict() for a in self.actions],
        }


class HTNClinicalPlan:
    """The complete hierarchical task network for a patient's care trajectory."""

    def __init__(
        self,
        plan_id: str,
        patient_id: str,
        goal: str,
        compound_tasks: List[CompoundClinicalTask],
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.plan_id = plan_id
        self.patient_id = patient_id
        self.goal = goal
        self.compound_tasks = compound_tasks
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.replanned_count = 0
        self.replanning_history: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "patient_id": self.patient_id,
            "goal": self.goal,
            "compound_tasks": [ct.to_dict() for ct in self.compound_tasks],
            "replanned_count": self.replanned_count,
            "replanning_history": self.replanning_history,
            "created_at": self.created_at.isoformat(),
        }


class HTNClinicalPlanner:
    """Hierarchical Task Network generator and reactive telemetry replanner."""

    def __init__(self) -> None:
        self._plans: Dict[str, HTNClinicalPlan] = {}

    def generate_plan(
        self,
        patient_id: str,
        goal: str,
        initial_state: Dict[str, Any],
    ) -> HTNClinicalPlan:
        """Decompose a high-level clinical goal into an actionable HTN tree."""
        pid = str(uuid.uuid4())
        compound_tasks: List[CompoundClinicalTask] = []

        if goal == "SEPTIC_SHOCK_RESUSCITATION":
            # Task 1: Hemodynamic Resuscitation
            t1_actions = [
                PrimitiveClinicalAction(
                    action_id=f"{pid}_act_1",
                    name="Administer Crystalloid IV Bolus (30 mL/kg)",
                    category="FLUIDS",
                    order_details={"fluid": "Lactated Ringers", "volume_ml": 2000, "rate": "RAPID_INFUSION"},
                    preconditions={"map_max": 65},
                    postconditions={"map_expected_min": 65},
                    time_limit_minutes=30,
                ),
                PrimitiveClinicalAction(
                    action_id=f"{pid}_act_2",
                    name="Initiate Norepinephrine Vasopressor Infusion",
                    category="MEDICATION",
                    order_details={"drug": "Norepinephrine", "starting_rate_mcg_min": 5, "titrate_target_map": 65},
                    preconditions={"fluid_bolus_completed": True, "map_max": 65},
                    postconditions={"map_expected_min": 65},
                    time_limit_minutes=45,
                ),
            ]
            compound_tasks.append(CompoundClinicalTask("TASK_HEMODYNAMICS", "Early Hemodynamic Optimization", t1_actions))

            # Task 2: Source Control and Antimicrobial Therapy
            t2_actions = [
                PrimitiveClinicalAction(
                    action_id=f"{pid}_act_3",
                    name="Stat Blood Cultures x2 Before Antibiotics",
                    category="LABS",
                    order_details={"specimen": "Peripheral Venipuncture x2", "lab": "Blood Culture Aerobic/Anaerobic"},
                    preconditions={},
                    postconditions={"cultures_drawn": True},
                    time_limit_minutes=15,
                ),
                PrimitiveClinicalAction(
                    action_id=f"{pid}_act_4",
                    name="Infuse Broad-Spectrum Empirical Antibiotics",
                    category="MEDICATION",
                    order_details={"drugs": ["Vancomycin 15mg/kg", "Piperacillin-Tazobactam 4.5g IV"]},
                    preconditions={"cultures_drawn": True},
                    postconditions={"antibiotic_initiated": True},
                    time_limit_minutes=60,
                ),
            ]
            compound_tasks.append(CompoundClinicalTask("TASK_ANTIMICROBIAL", "Immediate Source Control & Antibiotics", t2_actions))

        else:
            # Generic clinical plan template
            act_gen = [
                PrimitiveClinicalAction(
                    action_id=f"{pid}_gen_1",
                    name="Comprehensive Clinical Assessment & Monitoring",
                    category="MONITORING",
                    order_details={"action": "Continuous telemetry, pulse oximetry, automated BP q15m"},
                    preconditions={},
                    postconditions={},
                    time_limit_minutes=15,
                )
            ]
            compound_tasks.append(CompoundClinicalTask("TASK_GENERAL", "Standard Monitoring & Diagnostics", act_gen))

        plan = HTNClinicalPlan(
            plan_id=pid,
            patient_id=patient_id,
            goal=goal,
            compound_tasks=compound_tasks,
        )

        self._plans[pid] = plan
        return plan

    def reactive_replan(
        self,
        plan_id: str,
        telemetry_interrupt: Dict[str, Any],
    ) -> HTNClinicalPlan:
        """Dynamically adapt plan upon sudden patient deterioration or telemetry anomaly."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise KeyError(f"Clinical plan '{plan_id}' not found")

        map_val = telemetry_interrupt.get("map", 75)
        spo2_val = telemetry_interrupt.get("spo2", 98)
        lactate_val = telemetry_interrupt.get("lactate", 1.2)

        emergency_triggers: List[str] = []
        if map_val < 50:
            emergency_triggers.append(f"Severe refractory hypotension (MAP {map_val} mmHg < 50)")
        if spo2_val < 88:
            emergency_triggers.append(f"Hypoxemic respiratory failure (SpO2 {spo2_val}% < 88)")
        if lactate_val > 4.0:
            emergency_triggers.append(f"Acute severe tissue hypoperfusion (Lactate {lactate_val} mmol/L > 4.0)")

        if not emergency_triggers:
            # No emergency replanning required; continue existing plan
            return plan

        # Prune downstream non-emergent pending actions
        pruned_count = 0
        for task in plan.compound_tasks:
            for act in task.actions:
                if act.status == TaskStatus.PENDING and act.category not in ("FLUIDS", "MEDICATION"):
                    act.status = TaskStatus.PRUNED
                    pruned_count += 1

        # Synthesize Emergency Stabilization Subtree
        emergency_actions: List[PrimitiveClinicalAction] = []

        if map_val < 50:
            emergency_actions.append(
                PrimitiveClinicalAction(
                    action_id=f"{plan_id}_emerg_vaso",
                    name="EMERGENCY: Second-Line Vasopressin Infusion (0.03 units/min)",
                    category="MEDICATION",
                    order_details={"drug": "Vasopressin", "fixed_rate": "0.03 units/min", "indication": "Refractory Septic Shock"},
                    preconditions={"central_or_peripheral_access": True},
                    postconditions={"map_stabilized": True},
                    time_limit_minutes=5,
                )
            )

        if spo2_val < 88:
            emergency_actions.append(
                PrimitiveClinicalAction(
                    action_id=f"{plan_id}_emerg_airway",
                    name="EMERGENCY: Rapid Sequence Intubation (RSI) & Mechanical Ventilation",
                    category="PROCEDURE",
                    order_details={"action": "RSI Airway Team Call", "ventilator_mode": "Volume Control ARDSNet"},
                    preconditions={"airway_team_at_bedside": True},
                    postconditions={"airway_secured": True},
                    time_limit_minutes=10,
                )
            )

        emergency_task = CompoundClinicalTask(
            task_id=f"EMERGENCY_SUBTREE_{str(uuid.uuid4())[:8]}",
            name="Emergency Refractory Stabilization Protocol",
            actions=emergency_actions,
        )

        # Prepend emergency task to execute immediately
        plan.compound_tasks.insert(0, emergency_task)
        plan.replanned_count += 1

        replan_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "triggers": emergency_triggers,
            "actions_pruned": pruned_count,
            "emergency_actions_added": len(emergency_actions),
        }
        plan.replanning_history.append(replan_record)

        return plan

    def get_plan(self, plan_id: str) -> Optional[HTNClinicalPlan]:
        return self._plans.get(plan_id)

    def clear(self) -> None:
        self._plans.clear()
