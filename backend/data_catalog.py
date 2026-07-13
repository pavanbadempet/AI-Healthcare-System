"""
Data Catalog Service
====================
Provides a lightweight metadata catalog for dataset discovery, governance,
lineage, and freshness tracking (SLA). Persists metadata to a local JSON database.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CATALOG_FILE_PATH = Path("data/catalog/catalog.json")

@dataclass
class DatasetEntry:
    dataset_id: str
    name: str
    description: str
    owner: str
    schema: Dict[str, str]  # Field name -> Type string
    tags: List[str] = field(default_factory=list)
    sla_hours: float = 24.0
    freshness_field: str = "timestamp"
    quality_score: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    row_count: int = 0
    size_bytes: int = 0
    location: str = ""
    format: str = "json"  # parquet, delta, csv, json, sqlite

class DataCatalog:
    """Thread-safe singleton managing the data catalog and lineage records."""
    _instance: Optional[DataCatalog] = None
    _lock = threading.Lock()

    def __new__(cls) -> DataCatalog:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_catalog()
                cls._instance = inst
            return cls._instance

    def _init_catalog(self) -> None:
        self._lock = threading.Lock()
        self._catalog: Dict[str, DatasetEntry] = {}
        self._lineage: Dict[str, Dict[str, List[str]]] = {}  # dataset_id -> {"upstream": [...], "downstream": [...]}

        # Ensure parent directories exist
        CATALOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not self._db_load():
            self._load_from_disk()
        self._pre_register_default_datasets()

    def _load_from_disk(self) -> None:
        """Loads metadata from local JSON file."""
        if not CATALOG_FILE_PATH.exists():
            return
        try:
            with open(CATALOG_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                datasets = data.get("datasets", {})
                self._lineage = data.get("lineage", {})
                for k, v in datasets.items():
                    self._catalog[k] = DatasetEntry(**v)
        except Exception as e:
            logger.error("Failed to load data catalog: %s", e)

    def _save_to_disk(self) -> None:
        """Saves current state to local JSON file."""
        try:
            catalog_dict = {k: asdict(v) for k, v in self._catalog.items()}
            payload = {
                "datasets": catalog_dict,
                "lineage": self._lineage
            }
            with open(CATALOG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to write data catalog to disk: %s", e)

    def register_dataset(self, entry: DatasetEntry) -> None:
        """Registers or updates a dataset in the catalog."""
        with self._lock:
            entry.updated_at = datetime.now(timezone.utc).isoformat()
            self._catalog[entry.dataset_id] = entry
            if entry.dataset_id not in self._lineage:
                self._lineage[entry.dataset_id] = {"upstream": [], "downstream": [], "column_lineage": {}}

            self._db_save_dataset(entry)
            self._db_save_lineage(
                entry.dataset_id,
                self._lineage[entry.dataset_id]["upstream"],
                self._lineage[entry.dataset_id]["downstream"],
                self._lineage[entry.dataset_id].get("column_lineage", {})
            )
            self._save_to_disk()
            logger.info("Registered dataset: %s", entry.dataset_id)


    def get_dataset(self, dataset_id: str) -> Optional[DatasetEntry]:
        """Retrieves catalog metadata for a specific dataset ID."""
        with self._lock:
            return self._catalog.get(dataset_id)

    def update_quality_score(self, dataset_id: str, score: float) -> None:
        """Updates the computed quality score of a registered dataset."""
        with self._lock:
            entry = self._catalog.get(dataset_id)
            if entry:
                entry.quality_score = score
                entry.updated_at = datetime.now(timezone.utc).isoformat()
                self._db_save_dataset(entry)
                self._save_to_disk()
                logger.info("Updated quality score for %s to %.2f", dataset_id, score)

    def search_datasets(self, query: str, tags: Optional[List[str]] = None, owner: Optional[str] = None) -> List[DatasetEntry]:
        """Searches catalog by full text query, tags, or owner."""
        with self._lock:
            matches: List[DatasetEntry] = []
            query_lc = query.lower()
            for entry in self._catalog.values():
                # Text check
                text_match = (
                    query_lc in entry.dataset_id.lower() or
                    query_lc in entry.name.lower() or
                    query_lc in entry.description.lower()
                ) if query else True

                # Tag check
                tag_match = all(t in entry.tags for t in tags) if tags else True

                # Owner check
                owner_match = entry.owner.lower() == owner.lower() if owner else True

                if text_match and tag_match and owner_match:
                    matches.append(entry)
            return matches

    def add_lineage(self, upstream_id: str, downstream_id: str) -> None:
        """Adds a directed dependency edge between two datasets."""
        with self._lock:
            if upstream_id not in self._lineage:
                self._lineage[upstream_id] = {"upstream": [], "downstream": [], "column_lineage": {}}
            if downstream_id not in self._lineage:
                self._lineage[downstream_id] = {"upstream": [], "downstream": [], "column_lineage": {}}

            if downstream_id not in self._lineage[upstream_id]["downstream"]:
                self._lineage[upstream_id]["downstream"].append(downstream_id)
            if upstream_id not in self._lineage[downstream_id]["upstream"]:
                self._lineage[downstream_id]["upstream"].append(upstream_id)

            self._db_save_lineage(
                upstream_id,
                self._lineage[upstream_id]["upstream"],
                self._lineage[upstream_id]["downstream"],
                self._lineage[upstream_id].get("column_lineage", {})
            )
            self._db_save_lineage(
                downstream_id,
                self._lineage[downstream_id]["upstream"],
                self._lineage[downstream_id]["downstream"],
                self._lineage[downstream_id].get("column_lineage", {})
            )
            self._save_to_disk()

    def add_column_lineage(self, dataset_id: str, target_col: str, source_dataset: str, source_col: str, transform: str) -> None:
        """Adds column-level dependency information to a dataset's lineage metadata."""
        with self._lock:
            if dataset_id not in self._lineage:
                self._lineage[dataset_id] = {"upstream": [], "downstream": [], "column_lineage": {}}
            elif "column_lineage" not in self._lineage[dataset_id]:
                self._lineage[dataset_id]["column_lineage"] = {}

            self._lineage[dataset_id]["column_lineage"][target_col] = {
                "source_dataset": source_dataset,
                "source_column": source_col,
                "transform": transform
            }

            if source_dataset not in self._lineage[dataset_id]["upstream"]:
                self._lineage[dataset_id]["upstream"].append(source_dataset)
            if source_dataset not in self._lineage:
                self._lineage[source_dataset] = {"upstream": [], "downstream": [], "column_lineage": {}}
            if dataset_id not in self._lineage[source_dataset]["downstream"]:
                self._lineage[source_dataset]["downstream"].append(dataset_id)

            self._db_save_lineage(dataset_id, self._lineage[dataset_id]["upstream"], self._lineage[dataset_id]["downstream"], self._lineage[dataset_id]["column_lineage"])
            self._db_save_lineage(source_dataset, self._lineage[source_dataset]["upstream"], self._lineage[source_dataset]["downstream"], self._lineage[source_dataset].get("column_lineage", {}))
            self._save_to_disk()

    def get_lineage(self, dataset_id: str) -> Dict[str, Any]:
        """Returns direct upstream, downstream dependencies, and column lineage for a dataset."""
        with self._lock:
            lin = self._lineage.get(dataset_id, {"upstream": [], "downstream": [], "column_lineage": {}})
            if "column_lineage" not in lin:
                lin["column_lineage"] = {}
            return lin


    def get_stale_datasets(self, threshold_hours: Optional[float] = None) -> List[Dict[str, Any]]:
        """Finds datasets that have not been refreshed within their SLA hours."""
        with self._lock:
            stale = []
            now = datetime.now(timezone.utc)
            for entry in self._catalog.values():
                try:
                    last_update = datetime.fromisoformat(entry.updated_at)
                    diff = (now - last_update).total_seconds() / 3600.0
                    sla = threshold_hours if threshold_hours is not None else entry.sla_hours
                    if diff > sla:
                        stale.append({
                            "dataset_id": entry.dataset_id,
                            "last_updated": entry.updated_at,
                            "sla_hours": entry.sla_hours,
                            "elapsed_hours": round(diff, 1)
                        })
                except Exception:
                    pass
            return stale

    def _pre_register_default_datasets(self) -> None:
        """Seeds the catalog with standard healthcare datasets if they are missing."""
        defaults = [
            DatasetEntry(
                dataset_id="patient_accounts",
                name="Patient Accounts",
                description="Raw demographic and contact info (bronze layer)",
                owner="registration_service",
                schema={"id": "int", "username": "string", "email": "string", "dob": "string", "facility_id": "int"},
                tags=["bronze", "pii", "users"]
            ),
            DatasetEntry(
                dataset_id="encounters",
                name="Clinical Encounters",
                description="Records of patient visits and doctor consultations",
                owner="clinical_team",
                schema={"id": "int", "patient_id": "int", "department_id": "int", "start_time": "datetime", "status": "string"},
                tags=["bronze", "clinical"]
            ),
            DatasetEntry(
                dataset_id="vital_observations",
                name="Vital Observations",
                description="Streaming IoT / nurse check vital readings",
                owner="nursing_team",
                schema={"id": "int", "encounter_id": "int", "heart_rate": "float", "blood_pressure": "string", "temperature": "float"},
                tags=["bronze", "telemetry"]
            ),
            DatasetEntry(
                dataset_id="diagnostic_results",
                name="Diagnostic Results",
                description="Laboratory and radiology findings",
                owner="diagnostics_lab",
                schema={"id": "int", "encounter_id": "int", "test_type": "string", "result_value": "string", "is_normal": "bool"},
                tags=["bronze", "clinical"]
            ),
            DatasetEntry(
                dataset_id="prescriptions",
                name="Prescriptions",
                description="Medications prescribed by doctors to patients",
                owner="pharmacy_team",
                schema={"id": "int", "encounter_id": "int", "medication_name": "string", "dosage": "string", "is_dispensed": "bool"},
                tags=["bronze", "pharmacy"]
            ),
            DatasetEntry(
                dataset_id="invoices",
                name="Invoices",
                description="Billing records and claims",
                owner="billing_office",
                schema={"id": "int", "encounter_id": "int", "amount": "float", "payment_status": "string"},
                tags=["bronze", "finance"]
            ),
            DatasetEntry(
                dataset_id="silver_diabetes",
                name="Silver Diabetes Prediction Inputs",
                description="Cleaned, normalized data for diabetes inference modeling",
                owner="ml_platform",
                schema={"patient_id": "int", "pregnancies": "int", "glucose": "float", "insulin": "float", "bmi": "float"},
                tags=["silver", "ml", "features"],
                sla_hours=12.0
            ),
            DatasetEntry(
                dataset_id="silver_heart",
                name="Silver Heart Prediction Inputs",
                description="Cleaned, normalized data for heart risk prediction",
                owner="ml_platform",
                schema={"patient_id": "int", "age": "float", "sex": "int", "cholesterol": "float", "target": "int"},
                tags=["silver", "ml", "features"],
                sla_hours=12.0
            ),
            DatasetEntry(
                dataset_id="gold_health_insights",
                name="Gold Health Insights Datamart",
                description="Aggregated risk scores and telemetry metrics for clinical dashboards",
                owner="analytics_bi",
                schema={"facility_id": "int", "total_encounters": "int", "avg_diabetes_risk": "float", "avg_heart_risk": "float"},
                tags=["gold", "analytics", "dashboard"],
                sla_hours=6.0
            )
        ]

        for dataset in defaults:
            if dataset.dataset_id not in self._catalog:
                self._catalog[dataset.dataset_id] = dataset
                self._db_save_dataset(dataset)

        # Pre-wire lineage
        self._lineage.setdefault("patient_accounts", {"upstream": [], "downstream": [], "column_lineage": {}})
        self._lineage.setdefault("silver_diabetes", {"upstream": ["patient_accounts"], "downstream": ["gold_health_insights"], "column_lineage": {}})
        self._lineage.setdefault("silver_heart", {"upstream": ["patient_accounts"], "downstream": ["gold_health_insights"], "column_lineage": {}})
        self._lineage.setdefault("gold_health_insights", {"upstream": ["silver_diabetes", "silver_heart"], "downstream": [], "column_lineage": {}})

        # Populate sample column lineage
        self._lineage["silver_diabetes"]["column_lineage"] = {
            "patient_id": {"source_dataset": "patient_accounts", "source_column": "id", "transform": "direct"},
            "pregnancies": {"source_dataset": "patient_accounts", "source_column": "pregnancies", "transform": "direct"},
            "glucose": {"source_dataset": "patient_accounts", "source_column": "glucose", "transform": "anonymized"}
        }
        self._lineage["gold_health_insights"]["column_lineage"] = {
            "facility_id": {"source_dataset": "patient_accounts", "source_column": "facility_id", "transform": "direct"},
            "avg_diabetes_risk": {"source_dataset": "silver_diabetes", "source_column": "diabetes_risk", "transform": "aggregated"}
        }

        for dataset_id, lin in self._lineage.items():
            self._db_save_lineage(dataset_id, lin["upstream"], lin["downstream"], lin.get("column_lineage", {}))

        self._save_to_disk()


    def _db_load(self) -> bool:
        """Attempts to load datasets and lineage from the database. Returns True on success."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbDatasetEntry, DbDatasetLineage
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                db_datasets = db.query(DbDatasetEntry).all()
                for dbd in db_datasets:
                    entry = DatasetEntry(
                        dataset_id=dbd.dataset_id,
                        name=dbd.name,
                        description=dbd.description,
                        owner=dbd.owner,
                        schema=dbd.schema_definition,
                        tags=dbd.tags,
                        sla_hours=dbd.sla_hours,
                        freshness_field=dbd.freshness_field,
                        quality_score=dbd.quality_score,
                        created_at=dbd.created_at.isoformat() if dbd.created_at else None,
                        updated_at=dbd.updated_at.isoformat() if dbd.updated_at else None,
                        row_count=dbd.row_count,
                        size_bytes=dbd.size_bytes,
                        location=dbd.location,
                        format=dbd.format
                    )
                    self._catalog[entry.dataset_id] = entry

                db_lineages = db.query(DbDatasetLineage).all()
                self._lineage = {}
                for dbl in db_lineages:
                    self._lineage[dbl.dataset_id] = {
                        "upstream": dbl.upstream,
                        "downstream": dbl.downstream,
                        "column_lineage": dbl.column_lineage or {}
                    }
                logger.info("Successfully loaded data catalog from database.")
                return True
        except Exception as e:
            logger.warning("Failed to load catalog from database (falling back to JSON disk): %s", e)
            return False


    def _db_save_dataset(self, entry: DatasetEntry) -> bool:
        """Saves or updates a dataset catalog entry in the database."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbDatasetEntry
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                dbd = db.query(DbDatasetEntry).filter_by(dataset_id=entry.dataset_id).first()
                if not dbd:
                    dbd = DbDatasetEntry(dataset_id=entry.dataset_id)
                    db.add(dbd)
                dbd.name = entry.name
                dbd.description = entry.description
                dbd.owner = entry.owner
                dbd.schema_definition = entry.schema
                dbd.tags = entry.tags
                dbd.sla_hours = entry.sla_hours
                dbd.freshness_field = entry.freshness_field
                dbd.quality_score = entry.quality_score
                dbd.row_count = entry.row_count
                dbd.size_bytes = entry.size_bytes
                dbd.location = entry.location
                dbd.format = entry.format
                db.commit()
                return True
        except Exception as e:
            logger.warning("Failed to save dataset %s to database: %s", entry.dataset_id, e)
            return False

    def _db_save_lineage(self, dataset_id: str, upstream: List[str], downstream: List[str], column_lineage: Optional[Dict[str, Any]] = None) -> bool:
        """Saves dataset dependency lineage to the database."""
        try:
            from backend.database import get_db_context
            from backend.models.data_governance import DbDatasetLineage
        except ImportError:
            return False

        try:
            with get_db_context() as db:
                dbl = db.query(DbDatasetLineage).filter_by(dataset_id=dataset_id).first()
                if not dbl:
                    dbl = DbDatasetLineage(dataset_id=dataset_id)
                    db.add(dbl)
                dbl.upstream = upstream
                dbl.downstream = downstream
                if column_lineage is not None:
                    dbl.column_lineage = column_lineage
                db.commit()
                return True
        except Exception as e:
            logger.warning("Failed to save lineage for %s to database: %s", dataset_id, e)
            return False


# Global instance
data_catalog = DataCatalog()
