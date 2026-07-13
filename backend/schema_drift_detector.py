"""
Schema Drift Detector
=====================
Automated schema drift detection comparing Pydantic schemas, SQLAlchemy ORM
metadata models, and active database tables in SQL Server/Postgres/SQLite.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

@dataclass
class DriftItem:
    table_or_schema: str
    field: str
    drift_type: str  # ADDED, REMOVED, TYPE_CHANGED, CONSTRAINT_CHANGED
    source_a_value: Optional[str] = None
    source_b_value: Optional[str] = None
    severity: str = "WARNING"  # INFO, WARNING, CRITICAL

@dataclass
class DriftReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_a: str = ""
    source_b: str = ""
    drifts: List[DriftItem] = field(default_factory=list)

class SchemaDriftDetector:
    """Detects discrepancies between ORM models, Pydantic DTOs, and the relational DB schema."""

    def _normalize_type(self, type_str: str) -> str:
        """Maps vendor-specific and SQL dialect data types to canonical types."""
        t = type_str.split("(")[0].upper().strip()
        if any(x in t for x in ["INT", "SERIAL", "ROWID"]):
            return "INTEGER"
        if any(x in t for x in ["CHAR", "TEXT", "STRING", "JSON", "CLOB"]):
            return "VARCHAR"
        if any(x in t for x in ["FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL"]):
            return "DECIMAL"
        if any(x in t for x in ["BOOL", "BOOLEAN"]):
            return "BOOLEAN"
        if any(x in t for x in ["TIME", "DATE"]):
            return "TIMESTAMP"
        return t

    def compare_orm_to_database(self, engine: Engine, base: Type[DeclarativeBase]) -> DriftReport:
        """Inspects current DB connection and compares it against ORM class metadata."""
        report = DriftReport(source_a="ORM Metadata", source_b="Relational Database")

        try:
            inspector = inspect(engine)
            db_tables = inspector.get_table_names()

            # Map ORM metadata tables
            for table_name, table_obj in base.metadata.tables.items():
                if table_name not in db_tables:
                    report.drifts.append(
                        DriftItem(
                            table_or_schema=table_name,
                            field="*",
                            drift_type="REMOVED",
                            source_a_value="Table exists in ORM",
                            source_b_value="Table missing in Database",
                            severity="CRITICAL"
                        )
                    )
                    continue

                # Check columns
                db_cols = {c["name"]: c for c in inspector.get_columns(table_name)}
                for col_name, col_obj in table_obj.columns.items():
                    if col_name not in db_cols:
                        report.drifts.append(
                            DriftItem(
                                table_or_schema=table_name,
                                field=col_name,
                                drift_type="REMOVED",
                                source_a_value="Column exists in ORM",
                                source_b_value="Column missing in Database",
                                severity="CRITICAL"
                            )
                        )
                        continue

                    # Basic type validation using normalizer
                    orm_type_raw = str(col_obj.type)
                    db_type_raw = str(db_cols[col_name]["type"])

                    orm_norm = self._normalize_type(orm_type_raw)
                    db_norm = self._normalize_type(db_type_raw)

                    type_compat = (orm_norm == db_norm)

                    if not type_compat:
                        report.drifts.append(
                            DriftItem(
                                table_or_schema=table_name,
                                field=col_name,
                                drift_type="TYPE_CHANGED",
                                source_a_value=orm_type_raw,
                                source_b_value=db_type_raw,
                                severity="WARNING"
                            )
                        )

                    # Nullable check
                    if col_obj.nullable != db_cols[col_name]["nullable"]:
                        report.drifts.append(
                            DriftItem(
                                table_or_schema=table_name,
                                field=col_name,
                                drift_type="CONSTRAINT_CHANGED",
                                source_a_value=f"nullable={col_obj.nullable}",
                                source_b_value=f"nullable={db_cols[col_name]['nullable']}",
                                severity="INFO"
                            )
                        )
        except Exception as e:
            logger.error("Drift comparison ORM <-> DB failed: %s", e)
            report.drifts.append(
                DriftItem(
                    table_or_schema="*",
                    field="*",
                    drift_type="ERROR",
                    source_a_value="Execution error",
                    source_b_value=str(e),
                    severity="CRITICAL"
                )
            )

        return report

    def compare_pydantic_to_orm(self, pydantic_model: Type[BaseModel], orm_model: Any) -> DriftReport:
        """Verifies if Pydantic serializer fields match their corresponding ORM table columns."""
        report = DriftReport(
            source_a=f"Pydantic ({pydantic_model.__name__})",
            source_b=f"ORM ({orm_model.__name__})"
        )

        pydantic_fields = pydantic_model.model_fields
        orm_columns = orm_model.__table__.columns

        for field_name in pydantic_fields:
            if field_name not in orm_columns:
                report.drifts.append(
                    DriftItem(
                        table_or_schema=orm_model.__tablename__,
                        field=field_name,
                        drift_type="ADDED",
                        source_a_value="Present in API schema",
                        source_b_value="Missing in ORM columns",
                        severity="WARNING"
                    )
                )

        # Check required fields
        for col_name, col_obj in orm_columns.items():
            # If ORM column is not nullable, has no default value, and is missing in Pydantic create schemas
            if not col_obj.nullable and col_obj.default is None and col_obj.server_default is None and not col_obj.primary_key:
                if col_name not in pydantic_fields:
                    report.drifts.append(
                        DriftItem(
                            table_or_schema=orm_model.__tablename__,
                            field=col_name,
                            drift_type="REMOVED",
                            source_a_value="Missing in Pydantic schema",
                            source_b_value="Required in ORM",
                            severity="CRITICAL"
                        )
                    )

        return report

    def get_full_drift_report(self, engine: Engine, base: Type[DeclarativeBase]) -> List[DriftReport]:
        """Runs all comparisons and aggregates reports."""
        reports = []
        reports.append(self.compare_orm_to_database(engine, base))
        return reports

    def as_health_check(self, engine: Engine, base: Type[DeclarativeBase]) -> Dict[str, Any]:
        """Provides formatted dictionary output indicating schema drift status."""
        reports = self.get_full_drift_report(engine, base)
        critical_count = 0
        warning_count = 0
        drifts = []

        for r in reports:
            for d in r.drifts:
                drifts.append(asdict(d))
                if d.severity == "CRITICAL":
                    critical_count += 1
                elif d.severity == "WARNING":
                    warning_count += 1

        status = "healthy"
        if critical_count > 0:
            status = "critical"
        elif warning_count > 0:
            status = "degraded"

        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "critical_drifts": critical_count,
            "warning_drifts": warning_count,
            "drifts": drifts
        }

# Global instance
schema_drift_detector = SchemaDriftDetector()
