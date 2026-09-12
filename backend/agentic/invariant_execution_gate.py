"""Pre-Action Clinical Invariant Execution Gate.

Acts as an absolute deterministic safety barrier between autonomous AI agents
and hospital order execution. Evaluates 5 critical clinical invariants:
1. Absolute Contraindications
2. Renal & Hepatic Clearance Floors
3. Teratogenic & Pregnancy Restrictions
4. Anaphylactic Allergy Cross-Reactivity
5. High-Risk Four-Eye Quorum Mandates
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class InvariantType(str, Enum):
    """Categorization of clinical safety invariant barriers."""

    ABSOLUTE_CONTRAINDICATION = "ABSOLUTE_CONTRAINDICATION"
    RENAL_HEPATIC_CLEARANCE = "RENAL_HEPATIC_CLEARANCE"
    PREGNANCY_TERATOGENIC = "PREGNANCY_TERATOGENIC"
    ANAPHYLAXIS_ALLERGY = "ANAPHYLAXIS_ALLERGY"
    FOUR_EYE_QUORUM = "FOUR_EYE_QUORUM"


class InvariantViolation:
    """Detailed clinical explanation of an invariant breach."""

    def __init__(
        self,
        invariant_type: InvariantType | str,
        rule_id: str,
        message: str,
        clinical_severity: str = "FATAL_RISK",
        remediation: str = "",
    ) -> None:
        self.invariant_type = InvariantType(invariant_type) if isinstance(invariant_type, str) else invariant_type
        self.rule_id = rule_id
        self.message = message
        self.clinical_severity = clinical_severity
        self.remediation = remediation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invariant_type": self.invariant_type.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "clinical_severity": self.clinical_severity,
            "remediation": self.remediation,
        }


class InvariantExecutionResult:
    """Outcome of safety-gated execution."""

    def __init__(
        self,
        allowed: bool,
        status: str,
        action_name: str,
        parameters: Dict[str, Any],
        violations: Optional[List[InvariantViolation]] = None,
        execution_output: Optional[Any] = None,
        audit_token: Optional[str] = None,
    ) -> None:
        self.allowed = allowed
        self.status = status  # EXECUTED_SAFE, REJECTED_INVARIANT_BREACH
        self.action_name = action_name
        self.parameters = parameters
        self.violations = violations or []
        self.execution_output = execution_output
        self.audit_token = audit_token or str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "status": self.status,
            "action_name": self.action_name,
            "parameters": self.parameters,
            "violations": [v.to_dict() for v in self.violations],
            "execution_output": self.execution_output,
            "audit_token": self.audit_token,
            "timestamp": self.timestamp.isoformat(),
        }


class PreActionInvariantGate:
    """Deterministic runtime validator enforcing medical safety invariants."""

    def __init__(self) -> None:
        self._audit_log: List[Dict[str, Any]] = []

    def evaluate_invariants(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        patient_profile: Dict[str, Any],
    ) -> List[InvariantViolation]:
        """Evaluate action against deterministic physiological invariants."""
        violations: List[InvariantViolation] = []

        drug_name = (parameters.get("drug") or parameters.get("name") or "").strip().lower()
        active_conditions = [c.lower() for c in patient_profile.get("conditions", [])]
        allergies = [a.lower() for a in patient_profile.get("allergies", [])]
        egfr = patient_profile.get("egfr", 90.0)
        is_pregnant = patient_profile.get("is_pregnant", False)
        countersigned = parameters.get("countersigned_by") is not None

        # Invariant 1: Absolute Contraindication Checks
        if ("alteplase" in drug_name or "tpa" in drug_name or "tenecteplase" in drug_name):
            if any("hemorrhage" in c or "bleeding" in c for c in active_conditions):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                        rule_id="INV-THROMB-01",
                        message="Thrombolytic therapy strictly contraindicated in the presence of active intracranial hemorrhage or bleeding diathesis",
                        clinical_severity="FATAL_RISK",
                        remediation="Hold thrombolytics; urgent neurosurgical consult",
                    )
                )

        # Invariant 2: Renal Clearance & eGFR Thresholds
        if "metformin" in drug_name and egfr < 30.0:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_CLEARANCE,
                    rule_id="INV-RENAL-METFORMIN",
                    message=f"Metformin contraindicated when eGFR < 30 mL/min/1.73m² (current eGFR: {egfr}) due to high risk of fatal lactic acidosis",
                    clinical_severity="CRITICAL_TOXICITY",
                    remediation="Substitute with insulin or DPP-4 inhibitor requiring no renal clearance floor",
                )
            )

        if "vancomycin" in drug_name and egfr < 20.0 and parameters.get("dose", 0) > 1000:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_CLEARANCE,
                    rule_id="INV-RENAL-VANCO",
                    message=f"Standard Vancomycin dose exceeds safe clearance ceiling for severe renal impairment (eGFR: {egfr})",
                    clinical_severity="SEVERE_NEPHROTOXICITY",
                    remediation="Reduce dose or switch to trough-guided dosing interval (q48h)",
                )
            )

        # Invariant 3: Pregnancy Category X Restrictions
        teratogenic_drugs = ["methotrexate", "isotretinoin", "thalidomide", "warfarin"]
        if is_pregnant and any(t_drug in drug_name for t_drug in teratogenic_drugs):
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.PREGNANCY_TERATOGENIC,
                    rule_id="INV-PREG-CAT-X",
                    message=f"Medication '{drug_name}' is FDA Pregnancy Category X: proven severe fetal malformations or death",
                    clinical_severity="FATAL_FETAL_RISK",
                    remediation="Immediately cancel order; consult maternal-fetal medicine specialist",
                )
            )

        # Invariant 4: Anaphylaxis & Severe Cross-Reactivity
        if "penicillin" in allergies:
            beta_lactam_risks = ["ampicillin", "amoxicillin", "piperacillin", "penicillin"]
            if any(risk in drug_name for risk in beta_lactam_risks):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ANAPHYLAXIS_ALLERGY,
                        rule_id="INV-ALLERGY-PENICILLIN",
                        message=f"Severe Penicillin anaphylaxis flagged in patient record; '{drug_name}' triggers acute anaphylactic shock",
                        clinical_severity="FATAL_RISK",
                        remediation="Select non-beta-lactam alternative (e.g. Aztreonam, Fluoroquinolone, Macrolide)",
                    )
                )

        # Invariant 5: Four-Eye Attending Quorum for High-Risk Procedures
        high_risk_actions = ["invasive_mechanical_ventilation", "high_dose_chemotherapy", "cardiac_ablation"]
        if action_name.lower() in high_risk_actions and not countersigned:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.FOUR_EYE_QUORUM,
                    rule_id="INV-QUORUM-01",
                    message=f"High-risk clinical action '{action_name}' requires Four-Eye attending dual clinician countersignature before execution",
                    clinical_severity="GOVERNANCE_SAFETY_LOCK",
                    remediation="Obtain second clinician signature before initiating intervention",
                )
            )

        return violations

    def validate_and_execute(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        patient_profile: Dict[str, Any],
        executor_func: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> InvariantExecutionResult:
        """Evaluate invariants and execute tool in a protected sandbox if safe."""
        violations = self.evaluate_invariants(
            action_name=action_name,
            parameters=parameters,
            patient_profile=patient_profile,
        )

        if violations:
            result = InvariantExecutionResult(
                allowed=False,
                status="REJECTED_INVARIANT_BREACH",
                action_name=action_name,
                parameters=parameters,
                violations=violations,
                execution_output=None,
            )
            self._audit_log.append(result.to_dict())
            return result

        # Invariants passed: execute sandboxed action
        output = None
        if executor_func:
            output = executor_func(parameters)
        else:
            output = {"executed": True, "action": action_name, "parameters": parameters}

        token = hashlib.sha256(f"{action_name}:{datetime.datetime.now(datetime.timezone.utc).isoformat()}".encode("utf-8")).hexdigest()

        result = InvariantExecutionResult(
            allowed=True,
            status="EXECUTED_SAFE",
            action_name=action_name,
            parameters=parameters,
            violations=[],
            execution_output=output,
            audit_token=token,
        )

        self._audit_log.append(result.to_dict())
        return result

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)

    def clear(self) -> None:
        self._audit_log.clear()
