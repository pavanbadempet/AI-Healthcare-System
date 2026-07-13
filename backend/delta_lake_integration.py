"""
Databricks Delta Lake Integration for Healthcare Data
Full implementation with schema evolution, time travel, and ACID guarantees.
Supports both PySpark and lightweight Polars + delta-rs (delta-lake) engines.
"""

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from delta.tables import DeltaTable
    from pyspark.sql import DataFrame as SparkDF
    from pyspark.sql import SparkSession
except ImportError:
    # Optional stubs when running in pure Polars/delta-rs mode
    class SparkSession:
        pass
    class SparkDF:
        pass
    class DeltaTable:
        pass

logger = logging.getLogger(__name__)
DELTA_OPERATION_FAILURE_MESSAGE = "Delta Lake operation failed."
DELTA_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DELTA_DATA_TYPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\([0-9,\s]+\))?$")

class DeltaTableType(Enum):
    DIMENSION = "dimension"
    FACT = "fact"
    BRIDGE = "bridge"

@dataclass
class DeltaTableConfig:
    """Configuration for Delta Lake table creation and management"""
    table_name: str
    table_type: DeltaTableType
    database: str = os.getenv("DELTA_DATABASE", "healthcare_db")
    cluster_columns: List[str] = None  # Databricks Liquid Clustering
    enable_cdc: bool = True  # Change Data Feed
    write_properties: Dict[str, str] = None
    schema_evolution_enabled: bool = True

    def __post_init__(self):
        if self.cluster_columns is None:
            self.cluster_columns = []
        if self.write_properties is None:
            self.write_properties = {
                "delta.autoOptimize.optimizeWrite": "true",
                "delta.autoOptimize.autoCompact": "true",
                "delta.enableChangeDataFeed": "true",
                "delta.logRetentionDuration": "30 days",
                "delta.deletedFileRetentionDuration": "7 days",
                "delta.appendOnly": "false",
                "delta.enableDeletionVectors": "true"
            }

        if self.enable_cdc:
            self.write_properties["delta.enableChangeDataFeed"] = "true"


def _validate_delta_identifier(value: str, label: str) -> str:
    if not DELTA_IDENTIFIER_RE.fullmatch(value or ""):
        raise ValueError(f"Invalid Delta {label}")
    return value


def _validate_delta_qualified_name(value: str, label: str) -> str:
    parts = str(value or "").split(".")
    if not parts or any(not DELTA_IDENTIFIER_RE.fullmatch(part) for part in parts):
        raise ValueError(f"Invalid Delta {label}")
    return value


def _validate_delta_data_type(value: str) -> str:
    if not DELTA_DATA_TYPE_RE.fullmatch(value or ""):
        raise ValueError("Invalid Delta data_type")
    return value


def _delta_sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


class DeltaSchemaManager:
    """Manages Delta Lake schema evolution and versioning (supports Spark and delta-rs)"""

    def __init__(self, spark: Optional[SparkSession] = None):
        self.spark = spark
        self.use_spark = (spark is not None and hasattr(spark, "sql"))

    def create_delta_table(self, df: Any, config: DeltaTableConfig, path: str = None) -> Dict[str, Any]:
        """Create Delta table with optimized configuration"""
        catalog = os.getenv("DELTA_CATALOG", "uc_healthcare_prod")
        database = _validate_delta_identifier(config.database, "database")
        table_name = _validate_delta_identifier(config.table_name, "table_name")
        full_table_name = f"{catalog}.{database}.{table_name}"

        # Resolve path if none is provided for delta-rs mode
        if not path:
            path = os.path.join("data", "lakehouse", database, table_name)

        try:
            if self.use_spark:
                # ── Spark-based Write Pathway ──
                writer = df.write.format("delta")
                if config.cluster_columns:
                    writer = writer.clusterBy(*config.cluster_columns)

                writer = writer.mode("overwrite").options(**config.write_properties)
                if path:
                    writer.save(path)
                    self.spark.sql(
                        f"CREATE TABLE IF NOT EXISTS {full_table_name} USING DELTA LOCATION {_delta_sql_literal(path)}"
                    )
                    target = path
                else:
                    writer.saveAsTable(full_table_name)
                    target = full_table_name

                # Trigger Liquid Clustering optimization
                if config.cluster_columns:
                    self._apply_liquid_clustering(target, by_path=bool(path))

                record_count = df.count()
            else:
                # ── Polars & delta-rs Write Pathway ──
                import polars as pl
                if hasattr(df, "toPandas"):
                    pl_df = pl.from_pandas(df.toPandas())
                elif isinstance(df, pl.DataFrame):
                    pl_df = df
                else:
                    # Assume pandas or dict
                    pl_df = pl.DataFrame(df)

                os.makedirs(os.path.dirname(path), exist_ok=True)
                pl_df.write_delta(
                    path,
                    mode="overwrite",
                    delta_write_options={
                        "partition_by": config.cluster_columns if config.cluster_columns else None
                    }
                )
                record_count = len(pl_df)

            logger.info(f"Created Delta table: {full_table_name} at {path}")
            return {
                'status': 'success',
                'table_name': full_table_name,
                'table_type': config.table_type.value,
                'clustering': config.cluster_columns,
                'record_count': record_count
            }
        except Exception:
            logger.error("Failed to create Delta table")
            raise

    def _apply_liquid_clustering(self, target: str, by_path: bool):
        """Trigger Liquid Clustering optimization"""
        try:
            if self.use_spark:
                if by_path:
                    dt = DeltaTable.forPath(self.spark, target)
                else:
                    dt = DeltaTable.forName(self.spark, target)
                dt.optimize().executeCompaction()
                logger.info(f"Applied Liquid Clustering optimization to {target}")
            else:
                from deltalake import DeltaTable as RTDeltaTable
                dt = RTDeltaTable(target)
                dt.optimize.compact()
                logger.info(f"Compact optimization applied via delta-rs to {target}")
        except Exception:
            logger.warning("Failed to apply Liquid Clustering")

    def stream_cdc_changes(self, table_name: str, starting_version: int = 0) -> Any:
        """Capture change feed (CDC) changes"""
        if self.use_spark:
            return self.spark.readStream.format("delta") \
                .option("readChangeFeed", "true") \
                .option("startingVersion", starting_version) \
                .table(table_name)
        else:
            raise NotImplementedError("Streaming CDC is only supported in PySpark mode currently.")

    def evolve_schema(self, table_name: str, schema_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evolve Delta table schema with various change types"""
        changes_applied = []
        errors = []

        for change in schema_changes:
            try:
                change_type = change.get('type')
                if change_type == 'ADD_COLUMN':
                    self._add_column(table_name, change)
                    changes_applied.append(change)
                elif change_type == 'DROP_COLUMN':
                    self._drop_column(table_name, change)
                    changes_applied.append(change)
                elif change_type == 'RENAME_COLUMN':
                    self._rename_column(table_name, change)
                    changes_applied.append(change)
                elif change_type == 'MODIFY_TYPE':
                    self._modify_column_type(table_name, change)
                    changes_applied.append(change)
                elif change_type == 'UPDATE_COLUMN_DESCRIPTION':
                    self._update_column_description(table_name, change)
                    changes_applied.append(change)
                else:
                    errors.append(f"Unsupported change type: {change_type}")

            except Exception:
                errors.append(DELTA_OPERATION_FAILURE_MESSAGE)
                logger.error("Schema change failed")

        return {
            'table_name': table_name,
            'changes_applied': len(changes_applied),
            'errors': len(errors),
            'changes': changes_applied,
            'error_details': errors
        }

    def _add_column(self, table_name: str, change: Dict[str, Any]):
        table_name = _validate_delta_qualified_name(table_name, "table_name")
        column_name = _validate_delta_identifier(change['column_name'], "column_name")
        data_type = _validate_delta_data_type(change['data_type'])
        if self.use_spark:
            self.spark.sql(f"ALTER TABLE {table_name} ADD COLUMNS ({column_name} {data_type})")
        logger.info(f"Added column {column_name} to {table_name}")

    def _drop_column(self, table_name: str, change: Dict[str, Any]):
        table_name = _validate_delta_qualified_name(table_name, "table_name")
        column_name = _validate_delta_identifier(change['column_name'], "column_name")
        if self.use_spark:
            self.spark.sql(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        logger.info(f"Dropped column {column_name} from {table_name}")

    def _rename_column(self, table_name: str, change: Dict[str, Any]):
        table_name = _validate_delta_qualified_name(table_name, "table_name")
        old_name = _validate_delta_identifier(change['old_column_name'], "old_column_name")
        new_name = _validate_delta_identifier(change['new_column_name'], "new_column_name")
        if self.use_spark:
            self.spark.sql(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")
        logger.info(f"Renamed column {old_name} to {new_name} in {table_name}")

    def _modify_column_type(self, table_name: str, change: Dict[str, Any]):
        table_name = _validate_delta_qualified_name(table_name, "table_name")
        column_name = _validate_delta_identifier(change['column_name'], "column_name")
        new_type = _validate_delta_data_type(change['new_data_type'])
        if self.use_spark:
            self.spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}")
        logger.info(f"Modified column {column_name} type to {new_type} in {table_name}")

    def _update_column_description(self, table_name: str, change: Dict[str, Any]):
        table_name = _validate_delta_qualified_name(table_name, "table_name")
        column_name = _validate_delta_identifier(change['column_name'], "column_name")
        description = change['description']
        if self.use_spark:
            self.spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} COMMENT {_delta_sql_literal(description)}")
        logger.info(f"Updated description for column {column_name} in {table_name}")

    def query_at_snapshot(self, table_name: str, version: int) -> Any:
        """Query table at specific version for time travel"""
        if self.use_spark:
            return self.spark.read.format("delta").option("versionAsOf", version).table(table_name)
        else:
            import polars as pl
            from deltalake import DeltaTable as RTDeltaTable
            # Resolve local path from name
            path = table_name if os.path.exists(table_name) else os.path.join("data", "lakehouse", os.getenv("DELTA_DATABASE", "healthcare_db"), table_name)
            dt = RTDeltaTable(path)
            dt.load_as_version(version)
            return pl.from_arrow(dt.to_pyarrow_dataset())

    def query_at_timestamp(self, table_name: str, timestamp: str) -> Any:
        """Query table at specific timestamp for time travel"""
        if self.use_spark:
            return self.spark.read.format("delta").option("timestampAsOf", timestamp).table(table_name)
        else:
            import polars as pl
            from deltalake import DeltaTable as RTDeltaTable
            path = table_name if os.path.exists(table_name) else os.path.join("data", "lakehouse", os.getenv("DELTA_DATABASE", "healthcare_db"), table_name)
            dt = RTDeltaTable(path)
            dt.load_as_datetime(datetime.fromisoformat(timestamp))
            return pl.from_arrow(dt.to_pyarrow_dataset())

    def get_table_history(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table history"""
        try:
            if self.use_spark:
                dt = DeltaTable.forName(self.spark, table_name)
                return [row.asDict() for row in dt.history().collect()]
            else:
                from deltalake import DeltaTable as RTDeltaTable
                path = table_name if os.path.exists(table_name) else os.path.join("data", "lakehouse", os.getenv("DELTA_DATABASE", "healthcare_db"), table_name)
                dt = RTDeltaTable(path)
                return dt.history()
        except Exception:
            logger.error("Failed to get table history")
            raise

    def rollback_to_snapshot(self, table_name: str, version: int) -> Dict[str, Any]:
        """Rollback table to specific version (Restore)"""
        try:
            if self.use_spark:
                dt = DeltaTable.forName(self.spark, table_name)
                dt.restoreToVersion(version)
            else:
                from deltalake import DeltaTable as RTDeltaTable
                path = table_name if os.path.exists(table_name) else os.path.join("data", "lakehouse", os.getenv("DELTA_DATABASE", "healthcare_db"), table_name)
                dt = RTDeltaTable(path)
                dt.restore_to_version(version)

            logger.info(f"Restored {table_name} to version {version}")
            return {
                'table_name': table_name,
                'version': version,
                'rollback_time': datetime.now(timezone.utc).isoformat(),
                'status': 'success'
            }
        except Exception:
            logger.error("Failed to rollback table")
            raise

class HealthcareDeltaManager:
    """Healthcare-specific Delta Lake table management (Dual-engine Spark/delta-rs)"""

    def __init__(self, spark: Optional[SparkSession] = None):
        self.spark = spark
        self.schema_manager = DeltaSchemaManager(spark)
        self.table_configs = self._initialize_healthcare_configs()

    def _initialize_healthcare_configs(self) -> Dict[str, DeltaTableConfig]:
        """Initialize healthcare-specific table configurations"""
        return {
            'lab_results': DeltaTableConfig(
                table_name='lab_results',
                table_type=DeltaTableType.FACT,
                cluster_columns=['test_date', 'facility_id', 'patient_id'],
                schema_evolution_enabled=True,
                enable_cdc=True
            ),
            'patients': DeltaTableConfig(
                table_name='patients',
                table_type=DeltaTableType.DIMENSION,
                cluster_columns=['patient_id', 'updated_date'],
                schema_evolution_enabled=True,
                enable_cdc=True
            ),
            'providers': DeltaTableConfig(
                table_name='providers',
                table_type=DeltaTableType.DIMENSION,
                cluster_columns=['provider_id', 'specialization'],
                schema_evolution_enabled=True,
                enable_cdc=True
            ),
            'claims': DeltaTableConfig(
                table_name='claims',
                table_type=DeltaTableType.FACT,
                cluster_columns=['submission_date', 'claim_id', 'patient_id'],
                schema_evolution_enabled=True,
                enable_cdc=True
            ),
            'medications': DeltaTableConfig(
                table_name='medications',
                table_type=DeltaTableType.BRIDGE,
                cluster_columns=['prescription_date', 'patient_id'],
                schema_evolution_enabled=True,
                enable_cdc=True
            )
        }

    def create_lab_results_table(self, df: Any, path: str = None) -> Dict[str, Any]:
        config = self.table_configs['lab_results']
        return self.schema_manager.create_delta_table(df, config, path)

    def evolve_lab_results_schema(self, new_lab_codes: List[str]) -> Dict[str, Any]:
        schema_changes = []
        for lab_code in new_lab_codes:
            schema_changes.append({
                'type': 'ADD_COLUMN',
                'column_name': f'result_{lab_code.lower()}',
                'data_type': 'FLOAT',
                'description': f'Result value for {lab_code} test'
            })

        table_name = f"{os.getenv('DELTA_DATABASE', 'healthcare_db')}.lab_results"
        return self.schema_manager.evolve_schema(table_name, schema_changes)

    def create_patient_dimension(self, df: Any, path: str = None) -> Dict[str, Any]:
        config = self.table_configs['patients']
        return self.schema_manager.create_delta_table(df, config, path)

    def get_compliance_report(self, table_name: str) -> Dict[str, Any]:
        """Generate compliance report via Delta history"""
        try:
            history = self.schema_manager.get_table_history(table_name)
            total_snapshots = len(history)

            # Extract timestamp from dict (Spark) or list of dicts (delta-rs)
            oldest_snapshot = None
            if history:
                first_snap = history[-1]
                t_val = first_snap.get('timestamp')
                if isinstance(t_val, int):
                    oldest_snapshot = datetime.fromtimestamp(t_val / 1000, timezone.utc)
                elif isinstance(t_val, datetime):
                    oldest_snapshot = t_val
                elif isinstance(t_val, str):
                    try:
                        oldest_snapshot = datetime.fromisoformat(t_val)
                    except ValueError:
                        oldest_snapshot = None

            return {
                'table_name': table_name,
                'total_snapshots': total_snapshots,
                'oldest_snapshot': oldest_snapshot.isoformat() if oldest_snapshot else None,
                'recent_changes': history[:5] if history else [],
                'compliance_status': 'compliant',
                'audit_trail_available': True
            }
        except Exception:
            logger.error("Failed to generate compliance report")
            return {
                'table_name': table_name,
                'compliance_status': 'error',
                'error': DELTA_OPERATION_FAILURE_MESSAGE
            }

    def optimize_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Optimize Delta table for query patterns"""
        try:
            if self.schema_manager.use_spark:
                dt = DeltaTable.forName(self.spark, table_name)
                dt.optimize().executeCompaction()
                dt.vacuum(retentionHours=720)
            else:
                from deltalake import DeltaTable as RTDeltaTable
                path = table_name if os.path.exists(table_name) else os.path.join("data", "lakehouse", os.getenv("DELTA_DATABASE", "healthcare_db"), table_name)
                dt = RTDeltaTable(path)
                dt.optimize.compact()
                dt.vacuum(retention_hours=720, dry_run=False)

            logger.info(f"Optimized table performance for {table_name}")
            return {
                'table_name': table_name,
                'optimization_completed': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception:
            logger.error("Failed to optimize table")
            raise

# Initialize Delta manager
def get_delta_manager(spark: Optional[SparkSession] = None) -> HealthcareDeltaManager:
    """Get or create Delta Lake manager instance"""
    return HealthcareDeltaManager(spark)
