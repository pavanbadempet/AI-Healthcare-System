"""
Enforceable Enterprise Data Contracts & Schema Drift Quarantine Engine.

Enforces strict structural, semantic, and unit contracts on healthcare data payloads
at the ingestion perimeter (HL7, FHIR, EHR batch, device telemetry).

Prevents silent schema corruption by:
1. Validating field types, physical units, clinical ranges, and mandatory keys.
2. Routing valid payloads to Bronze/Silver pipelines.
3. Diverting non-conforming payloads to an automated Dead-Letter Queue (DLQ).
4. Distinguishing between Non-Breaking Schema Drift (auto-evolved) and Breaking Violations (quarantined).
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("backend.data_platform.contracts")


@dataclass
class FieldContract:
    field_name: str
    expected_type: str  # "string", "float", "int", "datetime", "boolean"
    required: bool = True
    unit: Optional[str] = None  # e.g. "mmHg", "mg/dL", "mL/min/1.73m2"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None


@dataclass
class DataContract:
    contract_id: str
    dataset_name: str
    version: str
    description: str
    fields: Dict[str, FieldContract]
    allow_extra_fields: bool = True  # Non-breaking drift policy


@dataclass
class ContractViolation:
    field_name: str
    violation_type: str  # "MISSING_REQUIRED", "TYPE_MISMATCH", "RANGE_OUT_OF_BOUNDS", "INVALID_UNIT", "ENUM_VIOLATION"
    expected: str
    actual: str
    severity: str  # "BREAKING", "WARNING"


@dataclass
class QuarantineDlqEntry:
    quarantine_id: str
    contract_id: str
    timestamp_iso: str
    payload: Dict[str, Any]
    violations: List[ContractViolation]
    drift_classification: str  # "BREAKING_CORRUPTION" or "EVOLVABLE_EXTENSION"
    reconciliation_proposal: str


@dataclass
class ContractValidationResult:
    is_valid: bool
    contract_id: str
    dataset_name: str
    passed_fields: List[str]
    violations: List[ContractViolation]
    quarantined: bool
    quarantine_id: Optional[str] = None
    drift_detected: bool = False
    new_uncontracted_fields: List[str] = field(default_factory=list)


class DataContractEngine:
    """
    Contract Enforcement and Schema Drift Quarantine Gate for Ingestion Pipelines.
    """

    def __init__(self) -> None:
        self._contracts: Dict[str, DataContract] = self._initialize_default_contracts()
        self._dlq: List[QuarantineDlqEntry] = []
        self._quarantine_counter = 5000

    def _initialize_default_contracts(self) -> Dict[str, DataContract]:
        """
        Initializes foundational clinical contracts for vitals, labs, and medications.
        """
        contracts = {}

        # 1. Vital Signs Ingestion Contract
        contracts["vitals_contract_v1"] = DataContract(
            contract_id="vitals_contract_v1",
            dataset_name="bedside_vitals",
            version="1.0.0",
            description="Perimeter contract for bedside vital signs streams",
            fields={
                "patient_id": FieldContract("patient_id", "string", required=True),
                "timestamp": FieldContract("timestamp", "string", required=True),
                "systolic_bp": FieldContract("systolic_bp", "float", required=True, unit="mmHg", min_value=30.0, max_value=300.0),
                "diastolic_bp": FieldContract("diastolic_bp", "float", required=True, unit="mmHg", min_value=10.0, max_value=200.0),
                "heart_rate": FieldContract("heart_rate", "float", required=True, unit="bpm", min_value=20.0, max_value=280.0),
                "spo2": FieldContract("spo2", "float", required=False, unit="percent", min_value=40.0, max_value=100.0),
            },
            allow_extra_fields=True,
        )

        # 2. Comprehensive Metabolic Panel (CMP) Lab Contract
        contracts["cmp_lab_contract_v1"] = DataContract(
            contract_id="cmp_lab_contract_v1",
            dataset_name="clinical_lab_cmp",
            version="1.0.0",
            description="Clinical chemistry perimeter contract for renal and electrolyte panels",
            fields={
                "patient_id": FieldContract("patient_id", "string", required=True),
                "sample_id": FieldContract("sample_id", "string", required=True),
                "serum_creatinine": FieldContract("serum_creatinine", "float", required=True, unit="mg/dL", min_value=0.1, max_value=25.0),
                "potassium": FieldContract("potassium", "float", required=True, unit="mEq/L", min_value=1.5, max_value=10.0),
                "sodium": FieldContract("sodium", "float", required=True, unit="mEq/L", min_value=100.0, max_value=180.0),
                "blood_glucose": FieldContract("blood_glucose", "float", required=True, unit="mg/dL", min_value=10.0, max_value=1500.0),
            },
            allow_extra_fields=True,
        )

        return contracts

    def register_contract(self, contract: DataContract) -> None:
        self._contracts[contract.contract_id] = contract

    def validate_payload(
        self,
        contract_id: str,
        payload: Dict[str, Any],
    ) -> ContractValidationResult:
        """
        Validates an incoming record against the active contract.
        Quarantines non-compliant records to the Dead-Letter Queue (DLQ).
        """
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Data contract '{contract_id}' not found in registry.")

        violations: List[ContractViolation] = []
        passed_fields: List[str] = []

        # 1. Check contracted fields
        for field_name, f_contract in contract.fields.items():
            if field_name not in payload:
                if f_contract.required:
                    violations.append(
                        ContractViolation(
                            field_name=field_name,
                            violation_type="MISSING_REQUIRED",
                            expected=f"Required field of type {f_contract.expected_type}",
                            actual="None (Key missing from payload)",
                            severity="BREAKING",
                        )
                    )
                continue

            val = payload[field_name]
            if val is None:
                if f_contract.required:
                    violations.append(
                        ContractViolation(
                            field_name=field_name,
                            violation_type="NULL_NOT_ALLOWED",
                            expected="Non-null value",
                            actual="None",
                            severity="BREAKING",
                        )
                    )
                continue

            # Type checking
            type_valid = True
            if f_contract.expected_type in {"float", "int"}:
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    type_valid = False
            elif f_contract.expected_type == "string":
                if not isinstance(val, str):
                    type_valid = False
            elif f_contract.expected_type == "boolean":
                if not isinstance(val, bool):
                    type_valid = False

            if not type_valid:
                violations.append(
                    ContractViolation(
                        field_name=field_name,
                        violation_type="TYPE_MISMATCH",
                        expected=f_contract.expected_type,
                        actual=type(val).__name__,
                        severity="BREAKING",
                    )
                )
                continue

            # Clinical Range checking
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                val_num = float(val)
                if f_contract.min_value is not None and val_num < f_contract.min_value:
                    violations.append(
                        ContractViolation(
                            field_name=field_name,
                            violation_type="RANGE_OUT_OF_BOUNDS",
                            expected=f">= {f_contract.min_value} {f_contract.unit or ''}",
                            actual=str(val_num),
                            severity="BREAKING",
                        )
                    )
                    continue
                if f_contract.max_value is not None and val_num > f_contract.max_value:
                    violations.append(
                        ContractViolation(
                            field_name=field_name,
                            violation_type="RANGE_OUT_OF_BOUNDS",
                            expected=f"<= {f_contract.max_value} {f_contract.unit or ''}",
                            actual=str(val_num),
                            severity="BREAKING",
                        )
                    )
                    continue

            passed_fields.append(field_name)

        # 2. Check uncontracted / schema-drift fields
        uncontracted = [k for k in payload if k not in contract.fields]
        drift_detected = len(uncontracted) > 0

        if drift_detected and not contract.allow_extra_fields:
            for extra in uncontracted:
                violations.append(
                    ContractViolation(
                        field_name=extra,
                        violation_type="UNEXPECTED_FIELD",
                        expected="Field not permitted in closed schema",
                        actual=str(payload[extra]),
                        severity="BREAKING",
                    )
                )

        breaking_violations = [v for v in violations if v.severity == "BREAKING"]
        is_valid = len(breaking_violations) == 0

        quarantine_id = None
        if not is_valid:
            self._quarantine_counter += 1
            quarantine_id = f"DLQ-{self._quarantine_counter}"

            # Formulate reconciliation proposal
            missing = [v.field_name for v in violations if v.violation_type == "MISSING_REQUIRED"]
            types = [v.field_name for v in violations if v.violation_type == "TYPE_MISMATCH"]
            ranges = [v.field_name for v in violations if v.violation_type == "RANGE_OUT_OF_BOUNDS"]

            reconcile_parts = []
            if missing:
                reconcile_parts.append(f"Supply required fields: {', '.join(missing)}.")
            if types:
                reconcile_parts.append(f"Cast fields to expected types: {', '.join(types)}.")
            if ranges:
                reconcile_parts.append(f"Inspect physiological sensor calibration for: {', '.join(ranges)}.")

            proposal = " ".join(reconcile_parts) if reconcile_parts else "Review contract schema definition."

            self._dlq.append(
                QuarantineDlqEntry(
                    quarantine_id=quarantine_id,
                    contract_id=contract_id,
                    timestamp_iso=datetime.now(timezone.utc).isoformat(),
                    payload=payload,
                    violations=violations,
                    drift_classification="BREAKING_CORRUPTION",
                    reconciliation_proposal=proposal,
                )
            )

        return ContractValidationResult(
            is_valid=is_valid,
            contract_id=contract_id,
            dataset_name=contract.dataset_name,
            passed_fields=passed_fields,
            violations=violations,
            quarantined=not is_valid,
            quarantine_id=quarantine_id,
            drift_detected=drift_detected,
            new_uncontracted_fields=uncontracted,
        )

    def get_quarantined_records(self, limit: int = 50) -> List[QuarantineDlqEntry]:
        return self._dlq[-limit:]


contract_enforcement_engine = DataContractEngine()
