"""
Databricks Delta Lake Integration for Healthcare Data
Full implementation with schema evolution, time travel, and ACID guarantees
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from pyspark.sql import SparkSession, DataFrame as SparkDF
from delta.tables import DeltaTable

logger = logging.getLogger(__name__)

class DeltaTableType(Enum):
    DIMENSION = "dimension"
    FACT = "fact"
    BRIDGE = "bridge"

@dataclass
class DeltaTableConfig:
    """Configuration for Delta Lake table creation and management"""
    table_name: str
    table_type: DeltaTableType
    database: str = "healthcare_db"
    cluster_columns: List[str] = None  # Databricks Liquid Clustering (Replaces static partitioning & Z-Ordering)
    enable_cdc: bool = True  # Native Change Data Feed for downstream Structured Streaming
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
                "delta.enableDeletionVectors": "true"  # High-performance MERGE operations
            }
        
        if self.enable_cdc:
            self.write_properties["delta.enableChangeDataFeed"] = "true"

class DeltaSchemaManager:
    """Manages Delta Lake schema evolution and versioning"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def create_delta_table(self, df: SparkDF, config: DeltaTableConfig, path: str = None) -> Dict[str, Any]:
        """Create Delta table with optimized configuration"""
        catalog = "uc_healthcare_prod" # Unity Catalog namespace
        full_table_name = f"{catalog}.{config.database}.{config.table_name}"
        
        try:
            # Write DataFrame as Delta table with Liquid Clustering
            writer = df.write.format("delta")
            
            # Liquid Clustering (Databricks / OSS Delta 3.0+)
            if config.cluster_columns:
                writer = writer.clusterBy(*config.cluster_columns)
            
            # Write with options
            writer = writer.mode("overwrite").options(**config.write_properties)
            
            if path:
                writer.save(path)
                self.spark.sql(f"CREATE TABLE IF NOT EXISTS {full_table_name} USING DELTA LOCATION '{path}'")
                target = path
            else:
                writer.saveAsTable(full_table_name)
                target = full_table_name
            
            # Trigger Liquid Clustering optimization
            if config.cluster_columns:
                self._apply_liquid_clustering(target, by_path=bool(path))
            
            logger.info(f"Created Unity Catalog Delta table: {full_table_name}")
            
            return {
                'status': 'success',
                'table_name': full_table_name,
                'table_type': config.table_type.value,
                'clustering': config.cluster_columns,
                'record_count': df.count()
            }
            
        except Exception as e:
            logger.error(f"Failed to create Delta table {full_table_name}: {e}")
            raise
    
    def _apply_liquid_clustering(self, target: str, by_path: bool):
        """Trigger Liquid Clustering to dynamically optimize data layout without full rewrites"""
        try:
            if by_path:
                dt = DeltaTable.forPath(self.spark, target)
            else:
                dt = DeltaTable.forName(self.spark, target)
            # Optimize triggers Liquid Clustering dynamically based on clusterBy schema
            dt.optimize().executeCompaction()
            logger.info(f"Applied Liquid Clustering optimization to {target}")
            
        except Exception as e:
            logger.warning(f"Failed to apply Liquid Clustering: {e}")
            
    def stream_cdc_changes(self, table_name: str, starting_version: int = 0) -> SparkDF:
        """Structured Streaming: Capture real-time Change Data Feed (CDC) for downstream pipelines"""
        return self.spark.readStream.format("delta") \
            .option("readChangeFeed", "true") \
            .option("startingVersion", starting_version) \
            .table(table_name)
            
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
                    
            except Exception as e:
                errors.append(f"Failed to apply {change_type}: {str(e)}")
                logger.error(f"Schema change failed: {e}")
        
        return {
            'table_name': table_name,
            'changes_applied': len(changes_applied),
            'errors': len(errors),
            'changes': changes_applied,
            'error_details': errors
        }
    
    def _add_column(self, table_name: str, change: Dict[str, Any]):
        column_name = change['column_name']
        data_type = change['data_type']
        self.spark.sql(f"ALTER TABLE {table_name} ADD COLUMNS ({column_name} {data_type})")
        logger.info(f"Added column {column_name} to {table_name}")
    
    def _drop_column(self, table_name: str, change: Dict[str, Any]):
        column_name = change['column_name']
        self.spark.sql(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        logger.info(f"Dropped column {column_name} from {table_name}")
    
    def _rename_column(self, table_name: str, change: Dict[str, Any]):
        old_name = change['old_column_name']
        new_name = change['new_column_name']
        self.spark.sql(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")
        logger.info(f"Renamed column {old_name} to {new_name} in {table_name}")
    
    def _modify_column_type(self, table_name: str, change: Dict[str, Any]):
        column_name = change['column_name']
        new_type = change['new_data_type']
        self.spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}")
        logger.info(f"Modified column {column_name} type to {new_type} in {table_name}")
    
    def _update_column_description(self, table_name: str, change: Dict[str, Any]):
        column_name = change['column_name']
        description = change['description']
        self.spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} COMMENT '{description}'")
        logger.info(f"Updated description for column {column_name} in {table_name}")
    
    def query_at_snapshot(self, table_name: str, version: int) -> SparkDF:
        """Query table at specific version for time travel"""
        return self.spark.read.format("delta").option("versionAsOf", version).table(table_name)
    
    def query_at_timestamp(self, table_name: str, timestamp: str) -> SparkDF:
        """Query table at specific timestamp for time travel"""
        return self.spark.read.format("delta").option("timestampAsOf", timestamp).table(table_name)
    
    def get_table_history(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table history via DeltaTable API"""
        try:
            dt = DeltaTable.forName(self.spark, table_name)
            return [row.asDict() for row in dt.history().collect()]
        except Exception as e:
            logger.error(f"Failed to get table history: {e}")
            return []
    
    def rollback_to_snapshot(self, table_name: str, version: int) -> Dict[str, Any]:
        """Rollback table to specific version (Restore)"""
        try:
            dt = DeltaTable.forName(self.spark, table_name)
            dt.restoreToVersion(version)
            logger.info(f"Restored {table_name} to version {version}")
            
            return {
                'table_name': table_name,
                'version': version,
                'rollback_time': datetime.now(timezone.utc).isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to rollback to version {version}: {e}")
            raise

class HealthcareDeltaManager:
    """Healthcare-specific Delta Lake table management"""
    
    def __init__(self, spark: SparkSession):
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
    
    def create_lab_results_table(self, df: SparkDF, path: str = None) -> Dict[str, Any]:
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
        
        table_name = "healthcare_db.lab_results"
        return self.schema_manager.evolve_schema(table_name, schema_changes)
    
    def create_patient_dimension(self, df: SparkDF, path: str = None) -> Dict[str, Any]:
        config = self.table_configs['patients']
        # Enable constraints if required
        return self.schema_manager.create_delta_table(df, config, path)
    
    def get_compliance_report(self, table_name: str) -> Dict[str, Any]:
        """Generate compliance report via Delta history"""
        try:
            history = self.schema_manager.get_table_history(table_name)
            total_snapshots = len(history)
            oldest_snapshot = min(snap['timestamp'] for snap in history) if history else None
            
            return {
                'table_name': table_name,
                'total_snapshots': total_snapshots,
                'oldest_snapshot': oldest_snapshot.isoformat() if oldest_snapshot else None,
                'recent_changes': history[:5] if history else [],
                'compliance_status': 'compliant',
                'audit_trail_available': True
            }
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                'table_name': table_name,
                'compliance_status': 'error',
                'error': str(e)
            }
    
    def optimize_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Optimize Delta table for healthcare query patterns"""
        try:
            dt = DeltaTable.forName(self.spark, table_name)
            
            # Compact small files
            dt.optimize().executeCompaction()
            
            # Expire old snapshots
            dt.vacuum(retentionHours=720) # 30 days
            
            logger.info(f"Optimized table performance for {table_name}")
            
            return {
                'table_name': table_name,
                'optimization_completed': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize table {table_name}: {e}")
            raise

# Initialize Delta manager
def get_delta_manager(spark: SparkSession) -> HealthcareDeltaManager:
    """Get or create Delta Lake manager instance"""
    return HealthcareDeltaManager(spark)
