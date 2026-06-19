"""
Advanced Data Modeling Framework
Databricks Delta Lake, Liquid Clustering, SCD Patterns, Schema Evolution
Enterprise-grade data modeling for healthcare analytics
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from delta.tables import DeltaTable
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from pyspark.sql.types import StructType

logger = logging.getLogger(__name__)
DATA_MODELING_FAILURE_MESSAGE = "Data modeling operation failed."

class TableFormat(Enum):
    DELTA = "delta"
    PARQUET = "parquet"
    HUDI = "hudi"

class SCDType(Enum):
    TYPE1 = 1  # Overwrite
    TYPE2 = 2  # Historical tracking
    TYPE3 = 3  # Hybrid (Partial history)

@dataclass
class DataModelConfig:
    """Configuration for data modeling patterns"""
    table_name: str
    table_format: TableFormat
    scd_type: SCDType
    cluster_columns: List[str]  # Replaces static partitions and Z-ordering
    enable_cdc: bool = True     # Enables Change Data Feed natively
    schema_evolution_enabled: bool = True
    time_travel_enabled: bool = True
    audit_columns: List[str] = field(default_factory=lambda: ['created_at', 'updated_at', 'is_current'])
    business_keys: List[str] = field(default_factory=list)
    tracking_columns: List[str] = field(default_factory=list)

@dataclass
class SchemaChange:
    """Schema change definition for evolution"""
    change_type: str  # ADD_COLUMN, DROP_COLUMN, MODIFY_TYPE, RENAME_COLUMN
    column_name: str
    new_column_name: Optional[str] = None
    old_data_type: Optional[str] = None
    new_data_type: Optional[str] = None
    default_value: Any = None
    nullable: bool = True

class DeltaLakeManager:
    """Delta Lake operations for ACID transactions and time travel"""

    def __init__(self, spark: SparkSession, table_path: str):
        self.spark = spark
        self.table_path = table_path
        self.table_name = os.path.basename(table_path)

    def create_delta_table(self, df: SparkDF, config: DataModelConfig) -> DeltaTable:
        """Create Delta table with optimized configuration"""
        # Configure Delta options
        delta_options = {
            "delta.autoOptimize.optimizeWrite": "true",
            "delta.autoOptimize.autoCompact": "true",
            "delta.enableChangeDataFeed": "true",
            "delta.logRetentionDuration": "30 days",
            "delta.deletedFileRetentionDuration": "7 days"
        }

        # Write to Delta Lake with Liquid Clustering
        df.write.format("delta") \
          .mode("overwrite") \
          .options(**delta_options) \
          .clusterBy(*config.cluster_columns) \
          .save(self.table_path)

        # Create Delta table object
        delta_table = DeltaTable.forPath(self.spark, self.table_path)

        # Trigger Liquid Clustering dynamically
        if config.cluster_columns:
            delta_table.optimize().executeCompaction()

        # Enforce storage-level data integrity constraints via Delta check constraints
        if config.table_name == "patients":
            try:
                self.spark.sql(f"ALTER TABLE delta.`{self.table_path}` ADD CONSTRAINT patient_id_not_null CHECK (patient_id IS NOT NULL)")
                logger.info(f"Added patient_id NOT NULL constraint to {self.table_name}")
            except Exception as e:
                logger.warning(f"Could not add patient_id constraint on Delta table: {e}")
        elif config.table_name == "lab_results":
            try:
                self.spark.sql(f"ALTER TABLE delta.`{self.table_path}` ADD CONSTRAINT result_value_non_negative CHECK (result_value >= 0)")
                logger.info(f"Added result_value >= 0 constraint to {self.table_name}")
            except Exception as e:
                logger.warning(f"Could not add result_value constraint on Delta table: {e}")

        logger.info(f"Created Delta table: {self.table_name}")
        return delta_table

    def upsert_to_delta(self, source_df: SparkDF, config: DataModelConfig,
                        condition: str) -> Dict[str, Any]:
        """Perform upsert (merge) operation with Delta Lake"""
        delta_table = DeltaTable.forPath(self.spark, self.table_path)

        start_time = datetime.now()

        # Build merge condition
        merge_condition = condition or self._build_merge_condition(config.business_keys)

        # Perform merge operation
        merge_builder = delta_table.alias("target").merge(
            source_df.alias("source"),
            merge_condition
        )

        # Configure merge based on SCD type
        if config.scd_type == SCDType.TYPE1:
            # Type 1: Update existing records
            merge_builder.whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

        elif config.scd_type == SCDType.TYPE2:
            # Type 2: Track history
            merge_builder.whenMatchedUpdate(
                set={"is_current": False, "updated_at": current_timestamp()}
            ).whenNotMatchedInsertAll().execute()

        elif config.scd_type == SCDType.TYPE3:
            # Type 3: Partial history tracking
            merge_builder.whenMatchedUpdate(
                set={
                    "is_current": False,
                    "updated_at": current_timestamp(),
                    **{f"previous_{col}": f"target.{col}" for col in config.tracking_columns}
                }
            ).whenNotMatchedInsertAll().execute()

        duration = (datetime.now() - start_time).total_seconds()

        # Get operation metrics
        metrics = delta_table.history().limit(1).collect()[0]

        return {
            'operation': 'upsert',
            'table': self.table_name,
            'duration_seconds': duration,
            'rows_affected': metrics['operationMetrics']['numOutputRows'],
            'files_added': metrics['operationMetrics'].get('numAddedFiles', 0),
            'files_removed': metrics['operationMetrics'].get('numRemovedFiles', 0)
        }

    def time_travel_query(self, timestamp: datetime = None, version: int = None) -> SparkDF:
        """Query historical data using Delta Lake time travel"""
        if timestamp:
            # Query by timestamp
            return self.spark.read.format("delta") \
                .option("timestampAsOf", timestamp.isoformat()) \
                .load(self.table_path)
        elif version:
            # Query by version
            return self.spark.read.format("delta") \
                .option("versionAsOf", version) \
                .load(self.table_path)
        else:
            raise ValueError("Either timestamp or version must be provided")

    def get_change_data_feed(self, start_version: int, end_version: int) -> SparkDF:
        """Get change data feed for CDC operations"""
        return self.spark.read.format("delta") \
            .option("readChangeFeed", "true") \
            .option("startingVersion", start_version) \
            .option("endingVersion", end_version) \
            .load(self.table_path)

    def optimize_table(self, config: DataModelConfig) -> Dict[str, Any]:
        """Optimize Delta table for performance"""
        delta_table = DeltaTable.forPath(self.spark, self.table_path)

        start_time = datetime.now()

        # Liquid Clustering dynamically groups data (Replaces Z-ordering)
        if config.cluster_columns:
            delta_table.optimize().executeCompaction()

        # Compact small files
        delta_table.optimize().executeCompaction()

        # Vacuum old files
        delta_table.vacuum(retentionHours=24)

        duration = (datetime.now() - start_time).total_seconds()

        return {
            'operation': 'optimize',
            'table': self.table_name,
            'duration_seconds': duration,
            'liquid_cluster_columns': config.cluster_columns
        }

    def _build_merge_condition(self, business_keys: List[str]) -> str:
        """Build merge condition from business keys"""
        conditions = []
        for key in business_keys:
            conditions.append(f"target.{key} = source.{key}")
        return " AND ".join(conditions)



class SCDManager:
    """Slowly Changing Dimensions (SCD) implementation"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def apply_scd_type1(self, source_df: SparkDF, target_table: str,
                       business_keys: List[str]) -> Dict[str, Any]:
        """Apply SCD Type 1: Overwrite existing records"""
        start_time = datetime.now()

        # Read existing data
        self.spark.table(target_table)

        # Build merge condition
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])

        # Perform merge (update)
        from delta.tables import DeltaTable
        delta_table = DeltaTable.forName(self.spark, target_table)

        delta_table.alias("target").merge(
            source_df.alias("source"),
            merge_condition
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

        duration = (datetime.now() - start_time).total_seconds()

        return {
            'scd_type': 1,
            'table': target_table,
            'duration_seconds': duration,
            'business_keys': business_keys
        }

    def apply_scd_type2(self, source_df: SparkDF, target_table: str,
                       business_keys: List[str], tracking_columns: List[str]) -> Dict[str, Any]:
        """Apply SCD Type 2: Track historical changes"""
        start_time = datetime.now()

        # Add audit columns to source
        source_with_audit = source_df.withColumn("is_current", lit(True)) \
                                   .withColumn("effective_date", current_timestamp()) \
                                   .withColumn("end_date", lit(None))

        # Read existing data
        self.spark.table(target_table)

        # Build merge condition
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])

        # Check for changes in tracking columns
        change_conditions = []
        for track_col in tracking_columns:
            change_conditions.append(f"target.{track_col} <> source.{track_col} OR (target.{track_col} IS NULL AND source.{track_col} IS NOT NULL) OR (target.{track_col} IS NOT NULL AND source.{track_col} IS NULL)")

        if change_conditions:
            merge_condition += f" AND ({' OR '.join(change_conditions)})"

        # Perform SCD Type 2 merge
        from delta.tables import DeltaTable
        delta_table = DeltaTable.forName(self.spark, target_table)

        delta_table.alias("target").merge(
            source_with_audit.alias("source"),
            merge_condition
        ).whenMatchedUpdate(
            set={
                "is_current": False,
                "end_date": current_timestamp(),
                "updated_at": current_timestamp()
            }
        ).whenNotMatchedInsertAll().execute()

        duration = (datetime.now() - start_time).total_seconds()

        return {
            'scd_type': 2,
            'table': target_table,
            'duration_seconds': duration,
            'business_keys': business_keys,
            'tracking_columns': tracking_columns
        }

    def apply_scd_type3(self, source_df: SparkDF, target_table: str,
                       business_keys: List[str], tracking_columns: List[str]) -> Dict[str, Any]:
        """Apply SCD Type 3: Partial history tracking"""
        start_time = datetime.now()

        # Add current values to previous values before update
        source_df = source_df.withColumn("updated_at", current_timestamp())

        # Read existing data
        self.spark.table(target_table)

        # Build merge condition
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in business_keys])

        # Check for changes
        change_conditions = []
        for track_col in tracking_columns:
            change_conditions.append(f"target.{track_col} <> source.{track_col}")

        if change_conditions:
            merge_condition += f" AND ({' OR '.join(change_conditions)})"

        # Prepare update set
        update_set = {"updated_at": current_timestamp()}
        for track_col in tracking_columns:
            update_set[f"previous_{track_col}"] = f"target.{track_col}"

        # Perform SCD Type 3 merge
        from delta.tables import DeltaTable
        delta_table = DeltaTable.forName(self.spark, target_table)

        delta_table.alias("target").merge(
            source_df.alias("source"),
            merge_condition
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

        duration = (datetime.now() - start_time).total_seconds()

        return {
            'scd_type': 3,
            'table': target_table,
            'duration_seconds': duration,
            'business_keys': business_keys,
            'tracking_columns': tracking_columns
        }

    def get_current_records(self, table_name: str) -> SparkDF:
        """Get current records from SCD table"""
        return self.spark.sql(f"SELECT * FROM {table_name} WHERE is_current = true")

    def get_historical_records(self, table_name: str, business_key_value: Any) -> SparkDF:
        """Get historical records for specific business key"""
        # This would need to be adapted based on the actual business key column
        return self.spark.sql(f"""
            SELECT * FROM {table_name}
            WHERE patient_id = '{business_key_value}'
            ORDER BY effective_date DESC
        """)

class SchemaEvolutionManager:
    """Schema evolution and versioning management"""

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.schema_registry = {}

    def register_schema(self, table_name: str, schema: StructType, version: int = 1):
        """Register schema version"""
        if table_name not in self.schema_registry:
            self.schema_registry[table_name] = {}

        self.schema_registry[table_name][version] = {
            'schema': schema,
            'registered_at': datetime.now(timezone.utc),
            'version': version
        }

    def detect_schema_changes(self, old_schema: StructType, new_schema: StructType) -> List[SchemaChange]:
        """Detect schema changes between versions"""
        changes = []

        old_fields = {field.name: field for field in old_schema.fields}
        new_fields = {field.name: field for field in new_schema.fields}

        # Check for added columns
        for field_name, new_field in new_fields.items():
            if field_name not in old_fields:
                changes.append(SchemaChange(
                    change_type="ADD_COLUMN",
                    column_name=field_name,
                    new_data_type=str(new_field.dataType),
                    nullable=new_field.nullable
                ))

        # Check for dropped columns
        for field_name in old_fields:
            if field_name not in new_fields:
                changes.append(SchemaChange(
                    change_type="DROP_COLUMN",
                    column_name=field_name
                ))

        # Check for modified columns
        for field_name in old_fields:
            if field_name in new_fields:
                old_field = old_fields[field_name]
                new_field = new_fields[field_name]

                if str(old_field.dataType) != str(new_field.dataType):
                    changes.append(SchemaChange(
                        change_type="MODIFY_TYPE",
                        column_name=field_name,
                        old_data_type=str(old_field.dataType),
                        new_data_type=str(new_field.dataType)
                    ))

        return changes

    def apply_schema_evolution(self, table_name: str, new_df: SparkDF,
                             table_format: TableFormat) -> Dict[str, Any]:
        """Apply schema evolution to table"""
        try:
            current_schema = self.spark.table(table_name).schema
            new_schema = new_df.schema

            # Detect changes
            changes = self.detect_schema_changes(current_schema, new_schema)

            if not changes:
                return {'status': 'no_changes', 'table': table_name}

            # Apply changes based on table format
            if table_format == TableFormat.DELTA:
                return self._apply_delta_evolution(table_name, changes)
            else:
                return {'status': 'unsupported_format', 'table': table_name}

        except Exception:
            logger.error("Schema evolution failed")
            return {'status': 'failed', 'table': table_name, 'error': DATA_MODELING_FAILURE_MESSAGE}

    def _apply_delta_evolution(self, table_name: str, changes: List[SchemaChange]) -> Dict[str, Any]:
        """Apply schema evolution for Delta Lake"""
        from delta.tables import DeltaTable

        DeltaTable.forName(self.spark, table_name)

        applied_changes = []

        for change in changes:
            try:
                if change.change_type == "ADD_COLUMN":
                    # Delta Lake automatically handles new columns
                    applied_changes.append(change.__dict__)
                else:
                    logger.warning(f"Delta Lake schema evolution for {change.change_type} not implemented")

            except Exception:
                logger.error("Failed to apply Delta schema change")

        return {
            'status': 'success',
            'table': table_name,
            'format': 'delta',
            'changes_applied': applied_changes
        }



    def get_schema_history(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema evolution history"""
        if table_name not in self.schema_registry:
            return []

        history = []
        for version, schema_info in self.schema_registry[table_name].items():
            history.append({
                'version': version,
                'registered_at': schema_info['registered_at'].isoformat(),
                'schema_fields': [field.name for field in schema_info['schema'].fields]
            })

        return sorted(history, key=lambda x: x['version'])

class HealthcareDataModeler:
    """Comprehensive data modeling for healthcare analytics"""

    def __init__(self, spark: SparkSession, warehouse_path: str):
        self.spark = spark
        self.warehouse_path = warehouse_path
        self.delta_manager = None
        self.scd_manager = SCDManager(spark)
        self.schema_manager = SchemaEvolutionManager(spark)

        # Initialize data model configurations
        self.model_configs = self._initialize_model_configs()

    def _initialize_model_configs(self) -> Dict[str, DataModelConfig]:
        """Initialize healthcare data model configurations"""
        return {
            'patients': DataModelConfig(
                table_name='patients',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                cluster_columns=['patient_id', 'updated_date'],
                business_keys=['patient_id'],
                tracking_columns=['email', 'phone', 'address'],
                enable_cdc=True
            ),
            'providers': DataModelConfig(
                table_name='providers',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                cluster_columns=['provider_id', 'specialization'],
                business_keys=['provider_id'],
                tracking_columns=['specialization', 'department', 'status'],
                enable_cdc=True
            ),
            'lab_results': DataModelConfig(
                table_name='lab_results',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE1,  # Lab results don't change
                cluster_columns=['test_date', 'facility_id', 'patient_id'],
                business_keys=['result_id'],
                enable_cdc=True
            ),
            'claims': DataModelConfig(
                table_name='claims',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                cluster_columns=['submission_date', 'claim_id', 'patient_id'],
                business_keys=['claim_id'],
                tracking_columns=['claim_status', 'paid_amount'],
                enable_cdc=True
            )
        }

    def create_patient_dimension(self, source_df: SparkDF) -> Dict[str, Any]:
        """Create patient dimension with SCD Type 2"""
        config = self.model_configs['patients']

        # Add audit columns
        patient_df = source_df.withColumn("updated_date", col("updated_at").cast("date")) \
                              .withColumn("is_current", lit(True)) \
                              .withColumn("effective_date", current_timestamp()) \
                              .withColumn("end_date", lit(None))

        # Create Delta table
        table_path = f"{self.warehouse_path}/patients"
        self.delta_manager = DeltaLakeManager(self.spark, table_path)

        if not os.path.exists(table_path):
            # Create new table
            self.delta_manager.create_delta_table(patient_df, config)
        else:
            # Apply SCD Type 2
            result = self.delta_manager.upsert_to_delta(patient_df, config, None)
            return result

        return {
            'status': 'success',
            'table': 'patients',
            'scd_type': 2,
            'records_processed': patient_df.count()
        }

    def create_lab_results_fact(self, source_df: SparkDF) -> Dict[str, Any]:
        """Create lab results fact table with Delta Lake"""
        config = self.model_configs['lab_results']
        table_path = f"{self.warehouse_path}/lab_results"

        self.delta_manager = DeltaLakeManager(self.spark, table_path)

        if not os.path.exists(table_path):
            self.delta_manager.create_delta_table(source_df, config)
        else:
            self.delta_manager.upsert_to_delta(source_df, config, None)

        return {
            'status': 'success',
            'table': 'lab_results',
            'format': 'delta',
            'records_processed': source_df.count()
        }

    def apply_schema_evolution_example(self) -> Dict[str, Any]:
        """Example of schema evolution for patient table"""
        # Simulate schema change: adding new column
        [
            SchemaChange(
                change_type="ADD_COLUMN",
                column_name="blood_type",
                new_data_type="STRING",
                nullable=True
            ),
            SchemaChange(
                change_type="ADD_COLUMN",
                column_name="emergency_contact",
                new_data_type="STRING",
                nullable=True
            )
        ]

        # Apply evolution via SchemaManager
        result = self.schema_manager.apply_schema_evolution(
            "patients",
            self.spark.createDataFrame([], StructType()), # Dummy DF in real usage
            TableFormat.DELTA
        )
        return result

    def get_data_lineage_report(self) -> Dict[str, Any]:
        """Generate comprehensive data lineage report"""
        lineage = {
            'tables': {},
            'relationships': [],
            'schema_history': {}
        }

        for table_name, config in self.model_configs.items():
            # Table metadata
            lineage['tables'][table_name] = {
                'format': config.table_format.value,
                'scd_type': config.scd_type.value,
                'liquid_clustering': config.cluster_columns,
                'business_keys': config.business_keys,
                'tracking_columns': config.tracking_columns,
                'cdc_enabled': config.enable_cdc
            }

            # Schema history
            lineage['schema_history'][table_name] = self.schema_manager.get_schema_history(table_name)

        # Add relationships (simplified example)
        lineage['relationships'] = [
            {'source': 'patients', 'target': 'lab_results', 'key': 'patient_id'},
            {'source': 'patients', 'target': 'claims', 'key': 'patient_id'},
            {'source': 'providers', 'target': 'lab_results', 'key': 'provider_id'},
            {'source': 'providers', 'target': 'claims', 'key': 'provider_id'}
        ]

        return lineage

# Initialize Spark session with Delta & Unity Catalog support
def create_spark_session_with_lakehouse() -> SparkSession:
    """Create Spark session with Databricks Delta Lake and Unity Catalog support"""
    spark = SparkSession.builder \
        .appName("HealthcareLakehouse") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.catalog.uc_healthcare_prod", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.delta.logStore.class", "org.apache.spark.sql.delta.storage.HDFSLogStore") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
        .getOrCreate()

    return spark

# Global data modeler instance
data_modeler = None

def get_data_modeler(spark: SparkSession, warehouse_path: str) -> HealthcareDataModeler:
    """Get or create data modeler instance"""
    global data_modeler
    if data_modeler is None:
        data_modeler = HealthcareDataModeler(spark, warehouse_path)
    return data_modeler
