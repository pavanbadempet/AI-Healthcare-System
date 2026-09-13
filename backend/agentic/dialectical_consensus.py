"""Dialectical Multi-Agent Clinical Consensus Engine.

Implements Dung's Abstract Argumentation Framework (AF = <A, R>) for multi-disciplinary
virtual tumor boards and acute clinical consensus, computing grounded and preferred
extensions to find mathematically undefeated, evidence-backed treatment plans.
"""

from __future__ import annotations

import datetime
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class SpecialistRole(str, Enum):
    """Specialist clinical personas participating in the dialectical deliberation."""

    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN"
    CLINICAL_PHARMACIST = "CLINICAL_PHARMACIST"
    MEDICAL_GENETICIST = "MEDICAL_GENETICIST"
    RADIOLOGIST_PATHOLOGIST = "RADIOLOGIST_PATHOLOGIST"
    MEDICAL_ETHICIST = "MEDICAL_ETHICIST"
    CRITICAL_CARE_SPECIALIST = "CRITICAL_CARE_SPECIALIST"
    INPATIENT_NURSE = "INPATIENT_NURSE"
    SURGICAL_SPECIALIST = "SURGICAL_SPECIALIST"


class ClinicalArgument:
    """A structured clinical claim backed by clinical reasoning and evidence."""

    def __init__(
        self,
        arg_id: str,
        agent_role: SpecialistRole | str,
        claim: str,
        rationale: str,
        evidence: Optional[List[str]] = None,
        confidence: float = 0.9,
    ) -> None:
        self.arg_id = arg_id
        self.agent_role = SpecialistRole(agent_role) if isinstance(agent_role, str) else agent_role
        self.claim = claim
        self.rationale = rationale
        self.evidence = evidence or []
        self.confidence = float(confidence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arg_id": self.arg_id,
            "agent_role": self.agent_role.value,
            "claim": self.claim,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


class ArgumentAttack:
    """An attack relation where an attacking argument refutes or constrains a target argument."""

    def __init__(
        self,
        attacker_id: str,
        target_id: str,
        attack_type: str,
        justification: str,
    ) -> None:
        self.attacker_id = attacker_id
        self.target_id = target_id
        self.attack_type = attack_type  # CONTRAINDICATION, DRUG_INTERACTION, GENOMIC_MISMATCH, ETHICAL_VETO
        self.justification = justification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "attack_type": self.attack_type,
            "justification": self.justification,
        }


class DungArgumentationFramework:
    """Formal implementation of Dung's Abstract Argumentation Framework (1995)."""

    def __init__(self) -> None:
        self.arguments: Dict[str, ClinicalArgument] = {}
        self.attacks: List[ArgumentAttack] = []

    def add_argument(self, argument: ClinicalArgument) -> None:
        self.arguments[argument.arg_id] = argument

    def add_attack(self, attacker_id: str, target_id: str, attack_type: str, justification: str) -> None:
        if attacker_id not in self.arguments:
            raise KeyError(f"Attacking argument '{attacker_id}' not found")
        if target_id not in self.arguments:
            raise KeyError(f"Target argument '{target_id}' not found")
        self.attacks.append(
            ArgumentAttack(
                attacker_id=attacker_id,
                target_id=target_id,
                attack_type=attack_type,
                justification=justification,
            )
        )

    def is_conflict_free(self, subset: Set[str]) -> bool:
        """Evaluate if no argument in subset attacks another argument in subset."""
        for att in self.attacks:
            if att.attacker_id in subset and att.target_id in subset:
                return False
        return True

    def get_attackers_of(self, arg_id: str) -> Set[str]:
        """Return all arguments that attack arg_id."""
        return {att.attacker_id for att in self.attacks if att.target_id == arg_id}

    def defends(self, subset: Set[str], arg_id: str) -> bool:
        """Evaluate if subset defends arg_id against all attackers.

        arg_id is defended by subset iff for every attacker b of arg_id,
        there is some argument c in subset that attacks b.
        """
        attackers = self.get_attackers_of(arg_id)
        for attacker in attackers:
            counter_attacked = any(
                att.attacker_id in subset and att.target_id == attacker
                for att in self.attacks
            )
            if not counter_attacked:
                return False
        return True

    def is_admissible(self, subset: Set[str]) -> bool:
        """Evaluate if subset is conflict-free and defends all of its elements."""
        if not self.is_conflict_free(subset):
            return False
        for arg_id in subset:
            if not self.defends(subset, arg_id):
                return False
        return True

    def is_complete_extension(self, subset: Set[str]) -> bool:
        """Evaluate if subset is an admissible set containing all arguments it defends."""
        if not self.is_admissible(subset):
            return False
        defended_by_subset = {a for a in self.arguments if self.defends(subset, a)}
        return subset == defended_by_subset

    def compute_grounded_extension(self) -> Set[str]:
        """Compute the unique Dung Grounded Extension via iterative characteristic fixed-point fold."""
        grounded: Set[str] = set()

        while True:
            # Characteristic function F(S) = {A in Args | S defends A}
            next_step: Set[str] = set()
            for arg_id in self.arguments:
                if self.defends(grounded, arg_id):
                    next_step.add(arg_id)

            if next_step == grounded:
                break
            grounded = next_step

        return grounded

    def compute_complete_extensions(self) -> List[Set[str]]:
        """Compute all complete extensions of the argumentation framework."""
        arg_list = sorted(list(self.arguments.keys()))
        n = len(arg_list)
        complete_extensions: List[Set[str]] = []

        def search(idx: int, current: Set[str]) -> None:
            if idx == n:
                if self.is_complete_extension(current):
                    complete_extensions.append(set(current))
                return

            # Branch 1: exclude arg_list[idx]
            search(idx + 1, current)

            # Branch 2: include arg_list[idx] if conflict-free
            cand = arg_list[idx]
            cand_set = current | {cand}
            if self.is_conflict_free(cand_set):
                search(idx + 1, cand_set)

        search(0, set())
        return complete_extensions

    def compute_preferred_extensions(self) -> List[Set[str]]:
        """Compute all preferred extensions (maximal admissible sets under set inclusion)."""
        arg_list = sorted(list(self.arguments.keys()))
        n = len(arg_list)
        admissible_sets: List[Set[str]] = []

        def search(idx: int, current: Set[str]) -> None:
            if idx == n:
                if self.is_admissible(current):
                    admissible_sets.append(set(current))
                return

            # Branch 1: exclude candidate
            search(idx + 1, current)

            # Branch 2: include candidate if conflict-free
            cand = arg_list[idx]
            cand_set = current | {cand}
            if self.is_conflict_free(cand_set):
                search(idx + 1, cand_set)

        search(0, set())

        # Filter for maximal admissible sets under set inclusion
        preferred: List[Set[str]] = []
        for s in admissible_sets:
            is_maximal = True
            for other in admissible_sets:
                if s < other:  # s is a strict subset of other
                    is_maximal = False
                    break
            if is_maximal and s not in preferred:
                preferred.append(s)

        if not preferred:
            preferred = [set()]
        return preferred


class DialecticalConsensusEngine:
    """Orchestrates multi-specialist clinical deliberation using Dung's argumentation theory."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def deliberate(
        self,
        patient_id: str,
        clinical_case: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a structured Virtual Tumor Board / ICU Multi-Disciplinary deliberation."""
        af = DungArgumentationFramework()

        # Extract case attributes
        biomarkers = clinical_case.get("biomarkers", {})
        patient_preferences = clinical_case.get("patient_preferences", {})

        # 1. Attending Physician Argument (Systemic Therapy Proposal)
        arg_physician = ClinicalArgument(
            arg_id="ARG_PHYSICIAN_01",
            agent_role=SpecialistRole.ATTENDING_PHYSICIAN,
            claim="Initiate standard Osimertinib targeted therapy",
            rationale="First-line standard of care for advanced adenocarcinoma",
            evidence=["NCCN Guidelines NSCLC v2.2026"],
            confidence=0.92,
        )
        af.add_argument(arg_physician)

        # 2. Geneticist Argument (Biomarker Analysis)
        egfr_status = biomarkers.get("EGFR")
        if egfr_status == "EXON_19_DEL":
            arg_geneticist = ClinicalArgument(
                arg_id="ARG_GENETICIST_01",
                agent_role=SpecialistRole.MEDICAL_GENETICIST,
                claim="Strongly endorse Osimertinib based on sensitizing EGFR Exon 19 Deletion",
                rationale="FLAURA study demonstrates superior progression-free survival",
                evidence=["NGS Panel Specimen GEN-8812"],
                confidence=0.96,
            )
            af.add_argument(arg_geneticist)
        elif egfr_status == "KRAS_G12C":
            arg_geneticist = ClinicalArgument(
                arg_id="ARG_GENETICIST_01",
                agent_role=SpecialistRole.MEDICAL_GENETICIST,
                claim="Oppose Osimertinib; initiate Sotorasib for KRAS G12C mutation",
                rationale="EGFR inhibitors ineffective against primary KRAS driver mutations",
                evidence=["NGS Panel Specimen GEN-8812"],
                confidence=0.95,
            )
            af.add_argument(arg_geneticist)
            af.add_attack(
                attacker_id="ARG_GENETICIST_01",
                target_id="ARG_PHYSICIAN_01",
                attack_type="GENOMIC_MISMATCH",
                justification="Tumor lacks sensitizing EGFR mutation; possesses KRAS G12C",
            )

        # 3. Clinical Pharmacist Argument (Safety, Organ Clearance, Drug-Drug Interactions)
        qt_interval = clinical_case.get("ecg_qtc", 430)
        current_meds = clinical_case.get("current_meds", [])

        if qt_interval > 480 or "Amiodarone" in current_meds:
            arg_pharmacist = ClinicalArgument(
                arg_id="ARG_PHARMACIST_01",
                agent_role=SpecialistRole.CLINICAL_PHARMACIST,
                claim="Hold Osimertinib due to high risk of fatal Torsades de Pointes (QTc prolongation)",
                rationale="Concurrent Amiodarone and baseline QTc > 480ms creates severe cardiotoxicity",
                evidence=["CPIC Pharmacogenomics Database", "CredibleMeds Category 1 QTc Risk"],
                confidence=0.98,
            )
            af.add_argument(arg_pharmacist)
            af.add_attack(
                attacker_id="ARG_PHARMACIST_01",
                target_id="ARG_PHYSICIAN_01",
                attack_type="DRUG_INTERACTION",
                justification="Severe additive QTc prolongation risk with current cardiology regimen",
            )

        # 4. Medical Ethicist Argument (Patient Directives & Autonomy)
        if patient_preferences.get("palliative_only") is True:
            arg_ethicist = ClinicalArgument(
                arg_id="ARG_ETHICIST_01",
                agent_role=SpecialistRole.MEDICAL_ETHICIST,
                claim="Pivot to symptom management and palliative hospice care",
                rationale="Patient has an active Advanced Health Care Directive declining toxic systemic antineoplastic therapy",
                evidence=["Advanced Directive executed 2026-01-15"],
                confidence=0.99,
            )
            af.add_argument(arg_ethicist)
            af.add_attack(
                attacker_id="ARG_ETHICIST_01",
                target_id="ARG_PHYSICIAN_01",
                attack_type="ETHICAL_VETO",
                justification="Patient explicitly declined aggressive chemotherapy/targeted interventions in notarized directive",
            )

        # Compute Grounded Consensus Extension
        grounded_ids = af.compute_grounded_extension()
        undefeated_arguments = [af.arguments[aid].to_dict() for aid in grounded_ids]
        defeated_arguments = [
            af.arguments[aid].to_dict()
            for aid in af.arguments
            if aid not in grounded_ids
        ]

        # Compute Preferred Extensions for multi-extension options
        preferred_ext_sets = af.compute_preferred_extensions()
        preferred_extensions_serialized = [
            [af.arguments[aid].to_dict() for aid in ext]
            for ext in preferred_ext_sets
        ]

        # Synthesize winning clinical recommendation
        if any(a["arg_id"] == "ARG_ETHICIST_01" for a in undefeated_arguments):
            consensus_action = "PIVOT_TO_PALLIATIVE_CARE"
            rationale_summary = "Patient autonomy directive overrides aggressive systemic therapy."
        elif any(a["arg_id"] == "ARG_PHARMACIST_01" for a in undefeated_arguments):
            consensus_action = "DEFER_TARGETED_THERAPY_CARDIAC_REVIEW"
            rationale_summary = "Critical QTc prolongation or drug interaction requires cardiology clearance before treatment."
        elif any(a["arg_id"] == "ARG_GENETICIST_01" and "Sotorasib" in a["claim"] for a in undefeated_arguments):
            consensus_action = "INITIATE_SOTORASIB_KRAS"
            rationale_summary = "Molecular genetics confirmed KRAS G12C target; EGFR therapy refuted."
        else:
            consensus_action = "PROCEED_WITH_STANDARD_TARGETED_THERAPY"
            rationale_summary = "All specialist checks passed with undefeated evidence-backed consensus."

        result = {
            "session_id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "consensus_action": consensus_action,
            "rationale_summary": rationale_summary,
            "grounded_consensus_arguments": undefeated_arguments,
            "defeated_arguments": defeated_arguments,
            "preferred_extensions": preferred_extensions_serialized,
            "attacks_evaluated": [att.to_dict() for att in af.attacks],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        self._history.append(result)
        return result

    def deliberate_proposals(
        self,
        patient_id: str,
        specialist_responses: List[Any],
        clinical_case: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deliberate across autonomous swarm responses using Dung's argumentation."""
        af = DungArgumentationFramework()
        case_info = clinical_case or {}

        # 1. Map each specialist response to ClinicalArguments
        for i, resp in enumerate(specialist_responses):
            agent_name = getattr(resp, "agent_name", None) or f"AGENT_{i+1}"
            role = SpecialistRole.ATTENDING_PHYSICIAN
            name_lower = agent_name.lower()
            if "pharmac" in name_lower:
                role = SpecialistRole.CLINICAL_PHARMACIST
            elif "genet" in name_lower or "tumor" in name_lower or "oncolog" in name_lower:
                role = SpecialistRole.MEDICAL_GENETICIST
            elif "radio" in name_lower or "path" in name_lower:
                role = SpecialistRole.RADIOLOGIST_PATHOLOGIST
            elif "ethic" in name_lower:
                role = SpecialistRole.MEDICAL_ETHICIST
            elif "nurs" in name_lower:
                role = SpecialistRole.INPATIENT_NURSE
            elif "icu" in name_lower or "triage" in name_lower or "emergency" in name_lower:
                role = SpecialistRole.CRITICAL_CARE_SPECIALIST

            confidence = getattr(resp, "epistemic_confidence", 0.9)
            recs = getattr(resp, "recommendations", [])
            claim_text = "; ".join(str(r) for r in recs) if recs else f"Recommendations by {agent_name}"
            rationale_text = getattr(resp, "reasoning", "") or f"Clinical reasoning by {agent_name}"

            arg = ClinicalArgument(
                arg_id=f"ARG_{agent_name.upper().replace(' ', '_')}_{i}",
                agent_role=role,
                claim=claim_text,
                rationale=rationale_text,
                confidence=confidence,
            )
            af.add_argument(arg)

        # 2. Add attacks based on clinical conflicts
        arg_ids = list(af.arguments.keys())
        for i, a_id in enumerate(arg_ids):
            a_arg = af.arguments[a_id]
            for j, b_id in enumerate(arg_ids):
                if i == j:
                    continue
                b_arg = af.arguments[b_id]
                # Check for pharmacological or ethical refutation
                claim_a = a_arg.claim.lower()
                claim_b = b_arg.claim.lower()
                if "hold" in claim_a or "contraindicated" in claim_a or "veto" in claim_a:
                    for target_kw in ["prescribe", "initiate", "give", "administer", "proceed"]:
                        if target_kw in claim_b:
                            role_title = a_arg.agent_role.value.replace('_', ' ').title()
                            af.add_attack(
                                attacker_id=a_id,
                                target_id=b_id,
                                attack_type="SAFETY_VETO",
                                justification=f"{role_title} vetoes proposed intervention in {b_id}",
                            )
                            break

        # Compute extensions
        grounded_ids = af.compute_grounded_extension()
        preferred_sets = af.compute_preferred_extensions()

        undefeated = [af.arguments[aid].to_dict() for aid in grounded_ids]
        defeated = [af.arguments[aid].to_dict() for aid in af.arguments if aid not in grounded_ids]
        preferred_serialized = [
            [af.arguments[aid].to_dict() for aid in ext]
            for ext in preferred_sets
        ]

        consensus_action = "PROCEED_WITH_CONSENSUS" if undefeated else "DISPUTE_REQUIRES_CLINICAL_REVIEW"
        if any("hold" in a["claim"].lower() or "veto" in a["claim"].lower() for a in undefeated):
            consensus_action = "SAFETY_HOLD_APPLIED"

        result = {
            "session_id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "consensus_action": consensus_action,
            "rationale_summary": f"Deliberated across {len(specialist_responses)} specialist swarm responses.",
            "grounded_consensus_arguments": undefeated,
            "defeated_arguments": defeated,
            "preferred_extensions": preferred_serialized,
            "attacks_evaluated": [att.to_dict() for att in af.attacks],
            "clinical_case": case_info,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._history.append(result)
        return result
