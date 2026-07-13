"""
Schema Contracts Service
========================
Defines and enforces formal schema contracts between data producers and
downstream consumers. Tracks schema version evolution and validation violations.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

REGISTRY_FILE_PATH = Path("data/contracts/registry.json")

@dataclass
class SchemaContract:
    contract_id: str
    name: str
    version: int
    producer: str
    consumer: str
    schema_definition: Dict[str, str]  # Field name -> Type string (e.g. int, float, string, bool)
    required_fields: List[str] = field(default_factory=list)
    compatibility_mode: str = "BACKWARD"  # BACKWARD, FORWARD, FULL, NONE
    sla_freshness_minutes: int = 1440
    quality_threshold: float = 0.95
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ContractRegistry:
    """Thread-safe singleton managing data schema contracts and monitoring compliance."""
    _instance: Optional[ContractRegistry] = None
    _lock = threading.Lock()

    def __new__(cls) -> ContractRegistry:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_registry()
                cls._instance = inst
            return cls._instance

    def _init_registry(self) -> None:
        self._lock = threading.Lock()
        self._contracts: Dict[str, SchemaContract] = {}
        self._violations: Dict[str, List[Dict[str, Any]]] = {}

        # Ensure folders exist
        REGISTRY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not self._db_load():
            self._load_from_disk()
        self._seed_default_contracts()

    def _load_from_disk(self) -> None:
        """Loads contracts from local JSON registry."""
        if not REGISTRY_FILE_PATH.exists():
            return
        try:
            with open(REGISTRY_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                contracts = data.get("contracts", {})
                self._violations = data.get("violations", {})
                for k, v in contracts.items():
                    self._contracts[k] = SchemaContract(**v)
        except Exception as e:
            logger.error("Failed to load schema contract registry: %s", e)

    def _save_to_disk(self) -> None:
        """Saves current state to registry file."""
        try:
            payload = {
                "contracts": {k: asdict(v) for k, v in self._contracts.items()},
                "violations": self._violations
            }
            with open(REGISTRY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to write contract registry to disk: %s", e)

    def register_contract(self, contract: SchemaContract) -> None:
        """Adds a new contract to the registry, executing compatibility checks if older versions exist."""
        with self._lock:
            old_contract = self._contracts.get(contract.contract_id)
            if old_contract:
                # Check compatibility before overriding
                compatible, message = self.check_compatibility(old_contract, contract)
                if not compatible:
                    logger.error("Schema evolution rejected: %s", message)
                    raise ValueError(f"Incompatible schema contract upgrade: {message}")

            contract.updated_at = datetime.now(timezone.utc).isoformat()
            self._contracts[contract.contract_id] = contract
            if contract.contract_id not in self._violations:
                self._violations[contract.contract_id] = []

            self._db_save_contract(contract)
            self._save_to_disk()
            logger.info("Registered contract %s (version: %d)", contract.contract_id, contract.version)

    def get_contract(self, contract_id: str) -> Optional[SchemaContract]:
        """Retrieves a schema contract by its ID."""
        with self._lock:
            return self._contracts.get(contract_id)

    def validate_data(self, contract_id: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validates incoming dataset dictionary or records against the registered contract."""
        with self._lock:
            contract = self._contracts.get(contract_id)

        if not contract:
            return {"valid": True, "message": "No contract registered, validation skipped."}

        records = [data] if isinstance(data, dict) else data
        errors = []

        for idx, record in enumerate(records):
            # Check required fields
            for field_name in contract.required_fields:
                if field_name not in record:
                    errors.append(f"Record {idx}: Missing required field '{field_name}'")
                    continue

            # Check type alignment
            for field_name, expected_type in contract.schema_definition.items():
                if field_name in record and record[field_name] is not None:
                    val = record[field_name]
                    actual_type = type(val).__name__

                    # Basic type mapping verification
                    type_align = False
                    if expected_type == "int" and isinstance(val, int) and not isinstance(val, bool):
                        type_align = True
                    elif expected_type == "float" and isinstance(val, (int, float)):
                        type_align = True
                    elif expected_type == "string" and isinstance(val, str):
                        type_align = True
                    elif expected_type == "bool" and isinstance(val, bool):
                        type_align = True

                    if not type_align:
                        errors.append(f"Record {idx}: Field '{field_name}' expects '{expected_type}', found '{actual_type}'")

        is_valid = len(errors) == 0
        if not is_valid:
            # Register violation in audit history
            with self._lock:
                self._violations[contract_id].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "errors": errors[:5],  # Cap log size
                    "record_count": len(records)
                })
                self._db_save_violation(contract_id, errors[:5], len(records))
                self._save_to_disk()
            logger.warning("Contract %s validation failed: %d issues", contract_id, len(errors))

        return {
            "valid": is_valid,
            "errors": errors,
            "validation_score": (len(records) - len(errors)) / len(records) if records else 1.0
        }

    def check_compatibility(self, old_contract: SchemaContract, new_contract: SchemaContract) -> Tuple[bool, str]:
        """Checks if a new contract schema conforms to compatibility configurations relative to the old schema."""
        mode = new_contract.compatibility_mode
        if mode == "NONE":
            return True, "None compatibility enforced"

        old_fields = old_contract.schema_definition
        new_fields = new_contract.schema_definition

        if mode in ("BACKWARD", "FULL"):
            # Backward: New schema can read old data.
            # Implies fields present in old schema must be present in new schema, or be nullable/optional.
            for field_name in old_contract.required_fields:
                if field_name not in new_fields:
                    return False, f"Backward incompatibility: Required field '{field_name}' removed."
                if old_fields[field_name] != new_fields[field_name]:
                    return False, f"Backward incompatibility: Type of field '{field_name}' changed from {old_fields[field_name]} to {new_fields[field_name]}."

        if mode in ("FORWARD", "FULL"):
            # Forward: Old schema can read new data.
            # Implies new required fields cannot be added unless they were already present.
            for field_name in new_contract.required_fields:
                if field_name not in old_fields:
                    return False, f"Forward incompatibility: New required field '{field_name}' added."

        return True, "Compatible"

    def get_violations(self, contract_id: str) -> List[Dict[str, Any]]:
        """Returns violation log for a contract."""
        with self._lock:
            return self._violations.get(contract_id, [])

    def evolve_contract(self, contract_id: str, changes: Dict[str, Any]) -> None:
        """Helper to create a new revision bump of a contract."""
        with self._lock:
            current = self._contracts.get(contract_id)
            if not current:
                raise ValueError(f"Contract {contract_id} does not exist to evolve.")

            evolved = SchemaContract(
                contract_id=contract_id,
                name=changes.get("name", current.name),
                version=current.version + 1,
                producer=changes.get("producer", current.producer),
                consumer=changes.get("consumer", current.consumer),
                schema_definition=changes.get("schema_definition", current.schema_definition),
                required_fields=changes.get("required_fields", current.required_fields),
                compatibility_mode=changes.get("compatibility_mode", current.compatibility_mode),
                sla_freshness_minutes=changes.get("sla_freshness_minutes", current.sla_freshness_minutes),
                quality_threshold=changes.get("quality_threshold", current.quality_threshold)
            )

        self.register_contract(evolved)

    def _seed_default_contracts(self) -> None:
        """Seeds initial data contracts if none exist."""
        defaults = [
            SchemaContract(
                contract_id="etl_patient_extract",
                name="ETL Patient Data Ingestion Contract",
                version=1,
                producer="registration_service",
                consumer="etl_pipeline",
                schema_definition={"id": "int", "username": "string", "email": "string", "facility_id": "int"},
                required_fields=["id", "username", "facility_id"]
            ),
            SchemaContract(
                contract_id="etl_lab_results",
                name="ETL Lab Results Pipeline Contract",
                version=1,
                producer="diagnostics_lab",
                consumer="etl_pipeline",
                schema_definition={"id": "int", "encounter_id": "int", "test_type": "string", "result_value": "string"},
                required_fields=["id", "encounter_id", "test_type"]
            ),
            SchemaContract(
                contract_id="prediction_input",
                name="Inference Prediction Inputs Contract",
                version=1,
                producer="frontend_service",
                consumer="ml_prediction_service",
                schema_definition={"pregnancies": "float", "glucose": "float", "insulin": "float", "bmi": "float"},
                required_fields=["glucose", "bmi"]
            )
        ]

        for contract in defaults:
            if contract.contract_id not in self._contracts:
                self._contracts[contract.contract_id] = contract
                self._db_save_contract(contract)

        self._save_to_disk()

    def _db_load(self) -> bool:
        """Attempts to load contracts and violations from the database. Returns True on success."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbContractViolation, DbSchemaContract
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                db_contracts = db.query(DbSchemaContract).all()
                for dbc in db_contracts:
                    contract = SchemaContract(
                        contract_id=dbc.contract_id,
                        name=dbc.name,
                        version=dbc.version,
                        producer=dbc.producer,
                        consumer=dbc.consumer,
                        schema_definition=dbc.schema_definition,
                        required_fields=dbc.required_fields,
                        compatibility_mode=dbc.compatibility_mode,
                        sla_freshness_minutes=dbc.sla_freshness_minutes,
                        quality_threshold=dbc.quality_threshold,
                        created_at=dbc.created_at.isoformat() if dbc.created_at else None,
                        updated_at=dbc.updated_at.isoformat() if dbc.updated_at else None
                    )
                    self._contracts[contract.contract_id] = contract

                db_violations = db.query(DbContractViolation).all()
                self._violations = {}
                for dbv in db_violations:
                    self._violations.setdefault(dbv.contract_id, []).append({
                        "timestamp": dbv.timestamp.isoformat() if dbv.timestamp else None,
                        "errors": dbv.errors,
                        "record_count": dbv.record_count
                    })
                logger.info("Successfully loaded data contracts from database.")
                return True
        except Exception as e:
            logger.warning("Failed to load contracts from database (falling back to JSON disk): %s", e)
            return False

    def _db_save_contract(self, contract: SchemaContract) -> bool:
        """Saves a contract definition to the database."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbSchemaContract
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                dbc = db.query(DbSchemaContract).filter_by(contract_id=contract.contract_id).first()
                if not dbc:
                    dbc = DbSchemaContract(contract_id=contract.contract_id)
                    db.add(dbc)
                dbc.name = contract.name
                dbc.version = contract.version
                dbc.producer = contract.producer
                dbc.consumer = contract.consumer
                dbc.schema_definition = contract.schema_definition
                dbc.required_fields = contract.required_fields
                dbc.compatibility_mode = contract.compatibility_mode
                dbc.sla_freshness_minutes = contract.sla_freshness_minutes
                dbc.quality_threshold = contract.quality_threshold
                db.commit()
                return True
        except Exception as e:
            logger.warning("Failed to save contract %s to database: %s", contract.contract_id, e)
            return False

    def _db_save_violation(self, contract_id: str, errors: List[str], record_count: int) -> bool:
        """Saves a validation violation record to the database."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbContractViolation
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                dbv = DbContractViolation(
                    contract_id=contract_id,
                    errors=errors,
                    record_count=record_count
                )
                db.add(dbv)
                db.commit()
                return True
        except Exception as e:
            logger.warning("Failed to save contract violation for %s to database: %s", contract_id, e)
            return False

# Global instance
contract_registry = ContractRegistry()
