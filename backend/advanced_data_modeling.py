"""
Advanced Data Modeling Framework
Delta Lake, Apache Iceberg, SCD Patterns, Schema Evolution
Enterprise-grade data modeling for healthcare analytics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from pyspark.sql import SparkSession, DataFrame as SparkDF
from pyspark.sql.functions import col, lit, current_timestamp
from pyspark.sql.types import StructType
from delta.tables import DeltaTable
import os

logger = logging.getLogger(__name__)

class TableFormat(Enum):
    DELTA = "delta"
    ICEBERG = "iceberg"
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
    partition_columns: List[str]
    sort_columns: List[str]
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
        
        # Write to Delta Lake
        df.write.format("delta") \
          .mode("overwrite") \
          .options(**delta_options) \
          .partitionBy(*config.partition_columns) \
          .save(self.table_path)
        
        # Create Delta table object
        delta_table = DeltaTable.forPath(self.spark, self.table_path)
        
        # Configure Z-ordering for performance
        if config.sort_columns:
            delta_table.optimize().executeZOrderBy(config.sort_columns)
        
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
        
        # Z-order optimization
        if config.sort_columns:
            delta_table.optimize().executeZOrderBy(config.sort_columns)
        
        # Compact small files
        delta_table.optimize().executeCompaction()
        
        # Vacuum old files
        delta_table.vacuum(retentionHours=24)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'operation': 'optimize',
            'table': self.table_name,
            'duration_seconds': duration,
            'z_order_columns': config.sort_columns
        }
    
    def _build_merge_condition(self, business_keys: List[str]) -> str:
        """Build merge condition from business keys"""
        conditions = []
        for key in business_keys:
            conditions.append(f"target.{key} = source.{key}")
        return " AND ".join(conditions)

class IcebergManager:
    """Apache Iceberg operations for table format evolution"""
    
    def __init__(self, spark: SparkSession, catalog_name: str = "healthcare_catalog"):
        self.spark = spark
        self.catalog_name = catalog_name
        
        # Configure Iceberg
        spark.conf.set("spark.sql.catalog." + catalog_name, "org.apache.iceberg.spark.SparkCatalog")
        spark.conf.set("spark.sql.catalog." + catalog_name + ".type", "hive")
        spark.conf.set("spark.sql.catalog." + catalog_name + ".warehouse", "s3://healthcare-warehouse/")
    
    def create_iceberg_table(self, df: SparkDF, table_name: str, 
                           config: DataModelConfig) -> Dict[str, Any]:
        """Create Iceberg table with schema evolution support"""
        namespace = f"{self.catalog_name}.healthcare_db"
        full_table_name = f"{namespace}.{table_name}"
        
        # Create Iceberg table
        df.write.format("iceberg") \
          .mode("overwrite") \
          .partitionBy(*config.partition_columns) \
          .saveAsTable(full_table_name)
        
        # Configure table properties
        self.spark.sql(f"""
            ALTER TABLE {full_table_name} 
            SET TBLPROPERTIES (
                'write.format.default' = 'parquet',
                'write.parquet.compression-codec' = 'snappy',
                'write.delete.mode' = 'merge-on-read',
                'write.update.mode' = 'merge-on-read',
                'write.merge.mode' = 'merge-on-read'
            )
        """)
        
        logger.info(f"Created Iceberg table: {full_table_name}")
        
        return {
            'table_name': full_table_name,
            'format': 'iceberg',
            'partitioning': config.partition_columns
        }
    
    def evolve_schema(self, table_name: str, schema_changes: List[SchemaChange]) -> Dict[str, Any]:
        """Evolve Iceberg table schema"""
        namespace = f"{self.catalog_name}.healthcare_db"
        full_table_name = f"{namespace}.{table_name}"
        
        changes_applied = []
        
        for change in schema_changes:
            try:
                if change.change_type == "ADD_COLUMN":
                    # Add new column
                    data_type = change.new_data_type or "STRING"
                    nullable_clause = "" if change.nullable else " NOT NULL"
                    default_clause = f" DEFAULT {change.default_value}" if change.default_value is not None else ""
                    
                    self.spark.sql(f"""
                        ALTER TABLE {full_table_name} 
                        ADD COLUMN {change.column_name} {data_type}{nullable_clause}{default_clause}
                    """)
                    
                elif change.change_type == "DROP_COLUMN":
                    # Drop column (with careful consideration)
                    self.spark.sql(f"""
                        ALTER TABLE {full_table_name} 
                        DROP COLUMN {change.column_name}
                    """)
                
                elif change.change_type == "MODIFY_TYPE":
                    # Modify column type (Iceberg supports this)
                    self.spark.sql(f"""
                        ALTER TABLE {full_table_name} 
                        ALTER COLUMN {change.column_name} TYPE {change.new_data_type}
                    """)
                
                elif change.change_type == "RENAME_COLUMN":
                    # Rename column
                    self.spark.sql(f"""
                        ALTER TABLE {full_table_name} 
                        RENAME COLUMN {change.old_column_name} TO {change.new_column_name}
                    """)
                
                changes_applied.append(change.__dict__)
                
            except Exception as e:
                logger.error(f"Failed to apply schema change {change.change_type}: {e}")
                continue
        
        return {
            'table_name': full_table_name,
            'changes_applied': changes_applied,
            'changes_count': len(changes_applied)
        }
    
    def get_table_history(self, table_name: str) -> List[Dict[str, Any]]:
        """Get Iceberg table history for audit"""
        namespace = f"{self.catalog_name}.healthcare_db"
        full_table_name = f"{namespace}.{table_name}"
        
        history_df = self.spark.sql(f"SELECT * FROM {full_table_name}.history")
        
        return [row.asDict() for row in history_df.collect()]
    
    def rollback_to_snapshot(self, table_name: str, snapshot_id: int) -> Dict[str, Any]:
        """Rollback table to specific snapshot"""
        namespace = f"{self.catalog_name}.healthcare_db"
        full_table_name = f"{namespace}.{table_name}"
        
        # Create rollback branch
        branch_name = f"rollback_{snapshot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.spark.sql(f"""
            ALTER TABLE {full_table_name} 
            CREATE BRANCH {branch_name} AS OF VERSION {snapshot_id}
        """)
        
        return {
            'table_name': full_table_name,
            'snapshot_id': snapshot_id,
            'branch_name': branch_name,
            'rollback_time': datetime.now().isoformat()
        }

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
            elif table_format == TableFormat.ICEBERG:
                return self._apply_iceberg_evolution(table_name, changes)
            else:
                return {'status': 'unsupported_format', 'table': table_name}
                
        except Exception as e:
            logger.error(f"Schema evolution failed for {table_name}: {e}")
            return {'status': 'failed', 'table': table_name, 'error': str(e)}
    
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
                    
            except Exception as e:
                logger.error(f"Failed to apply Delta schema change: {e}")
        
        return {
            'status': 'success',
            'table': table_name,
            'format': 'delta',
            'changes_applied': applied_changes
        }
    
    def _apply_iceberg_evolution(self, table_name: str, changes: List[SchemaChange]) -> Dict[str, Any]:
        """Apply schema evolution for Iceberg"""
        # This would use the IcebergManager
        ice_manager = IcebergManager(self.spark)
        
        table_short_name = table_name.split('.')[-1]
        result = ice_manager.evolve_schema(table_short_name, changes)
        
        return {
            'status': 'success',
            'table': table_name,
            'format': 'iceberg',
            **result
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
        self.iceberg_manager = IcebergManager(spark)
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
                partition_columns=['updated_date'],
                sort_columns=['patient_id'],
                business_keys=['patient_id'],
                tracking_columns=['email', 'phone', 'address']
            ),
            'providers': DataModelConfig(
                table_name='providers',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                partition_columns=['specialization'],
                sort_columns=['provider_id'],
                business_keys=['provider_id'],
                tracking_columns=['specialization', 'department', 'status']
            ),
            'lab_results': DataModelConfig(
                table_name='lab_results',
                table_format=TableFormat.ICEBERG,
                scd_type=SCDType.TYPE1,  # Lab results don't change
                partition_columns=['test_date', 'facility_id'],
                sort_columns=['result_id'],
                business_keys=['result_id']
            ),
            'claims': DataModelConfig(
                table_name='claims',
                table_format=TableFormat.DELTA,
                scd_type=SCDType.TYPE2,
                partition_columns=['submission_date'],
                sort_columns=['claim_id'],
                business_keys=['claim_id'],
                tracking_columns=['claim_status', 'paid_amount']
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
        """Create lab results fact table with Iceberg"""
        config = self.model_configs['lab_results']
        
        # Create Iceberg table
        result = self.iceberg_manager.create_iceberg_table(source_df, 'lab_results', config)
        
        return {
            'status': 'success',
            'table': 'lab_results',
            'format': 'iceberg',
            'records_processed': source_df.count(),
            **result
        }
    
    def apply_schema_evolution_example(self) -> Dict[str, Any]:
        """Example of schema evolution for patient table"""
        # Simulate schema change: adding new column
        new_schema_changes = [
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
        
        # Apply evolution
        result = self.iceberg_manager.evolve_schema('patients', new_schema_changes)
        
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
                'partitioning': config.partition_columns,
                'business_keys': config.business_keys,
                'tracking_columns': config.tracking_columns
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

# Initialize Spark session with Delta and Iceberg support
def create_spark_session_with_lakehouse() -> SparkSession:
    """Create Spark session with Delta Lake and Iceberg support"""
    spark = SparkSession.builder \
        .appName("HealthcareLakehouse") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "file:///tmp/iceberg-warehouse") \
        .config("spark.delta.logStore.class", "org.apache.spark.sql.delta.storage.HDFSLogStore") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
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
