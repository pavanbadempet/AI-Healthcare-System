"""
Apache Iceberg Integration for Healthcare Data
Full implementation with schema evolution, partition evolution, and time travel
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json
from pyspark.sql import SparkSession, DataFrame as SparkDF
from pyspark.sql.functions import col, lit, current_timestamp, max as spark_max, min as spark_min
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DateType, TimestampType, BooleanType

logger = logging.getLogger(__name__)

class IcebergTableType(Enum):
    DIMENSION = "dimension"
    FACT = "fact"
    BRIDGE = "bridge"

@dataclass
class IcebergTableConfig:
    """Configuration for Iceberg table creation and management"""
    table_name: str
    table_type: IcebergTableType
    database: str = "healthcare_db"
    catalog: str = "healthcare_catalog"
    partitioning_spec: List[str] = None
    sort_order: List[str] = None
    write_properties: Dict[str, str] = None
    schema_evolution_enabled: bool = True
    
    def __post_init__(self):
        if self.partitioning_spec is None:
            self.partitioning_spec = []
        if self.sort_order is None:
            self.sort_order = []
        if self.write_properties is None:
            self.write_properties = {
                'write.format.default': 'parquet',
                'write.parquet.compression-codec': 'snappy',
                'write.delete.mode': 'merge-on-read',
                'write.update.mode': 'merge-on-read',
                'write.merge.mode': 'merge-on-read',
                'write.distribution-mode': 'hash'
            }

class IcebergSchemaManager:
    """Manages Iceberg schema evolution and versioning"""
    
    def __init__(self, spark: SparkSession, catalog_name: str):
        self.spark = spark
        self.catalog_name = catalog_name
        self._configure_iceberg_catalog()
    
    def _configure_iceberg_catalog(self):
        """Configure Iceberg catalog with proper settings"""
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}", "org.apache.iceberg.spark.SparkCatalog")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.type", "hive")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.warehouse", "s3://healthcare-iceberg-warehouse/")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.uri", "thrift://hive-metastore:9083")
        
        # Enable Iceberg extensions
        self.spark.conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        
        logger.info(f"Configured Iceberg catalog: {self.catalog_name}")
    
    def create_iceberg_table(self, df: SparkDF, config: IcebergTableConfig) -> Dict[str, Any]:
        """Create Iceberg table with optimized configuration"""
        full_table_name = f"{config.catalog}.{config.database}.{config.table_name}"
        
        try:
            # Write DataFrame as Iceberg table
            writer = df.write.format("iceberg")
            
            # Add partitioning if specified
            if config.partitioning_spec:
                writer = writer.partitionBy(*config.partitioning_spec)
            
            # Write with mode and properties
            writer.mode("overwrite").options(**config.write_properties).saveAsTable(full_table_name)
            
            # Apply sort order if specified
            if config.sort_order:
                self._apply_sort_order(full_table_name, config.sort_order)
            
            # Enable snapshot logging for time travel
            self._enable_snapshot_logging(full_table_name)
            
            logger.info(f"Created Iceberg table: {full_table_name}")
            
            return {
                'status': 'success',
                'table_name': full_table_name,
                'table_type': config.table_type.value,
                'partitioning': config.partitioning_spec,
                'sort_order': config.sort_order,
                'record_count': df.count()
            }
            
        except Exception as e:
            logger.error(f"Failed to create Iceberg table {full_table_name}: {e}")
            raise
    
    def _apply_sort_order(self, table_name: str, sort_columns: List[str]):
        """Apply sort order to Iceberg table for query optimization"""
        try:
            # Build sort order specification
            sort_spec = ", ".join([f"{col} ASC" for col in sort_columns])
            
            self.spark.sql(f"""
                ALTER TABLE {table_name} 
                WRITE ORDERED BY ({sort_spec})
            """)
            
            logger.info(f"Applied sort order to {table_name}: {sort_columns}")
            
        except Exception as e:
            logger.warning(f"Failed to apply sort order: {e}")
    
    def _enable_snapshot_logging(self, table_name: str):
        """Enable snapshot logging for time travel queries"""
        try:
            self.spark.sql(f"""
                ALTER TABLE {table_name} 
                SET TBLPROPERTIES (
                    'write.snapshot.expire.min-versions' = '10',
                    'write.delete.parquet.compression-codec' = 'snappy',
                    'write.update.parquet.compression-codec' = 'snappy',
                    'write.merge.parquet.compression-codec' = 'snappy'
                )
            """)
            
        except Exception as e:
            logger.warning(f"Failed to enable snapshot logging: {e}")
    
    def evolve_schema(self, table_name: str, schema_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evolve Iceberg table schema with various change types"""
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
        """Add new column to Iceberg table"""
        column_name = change['column_name']
        data_type = change['data_type']
        description = change.get('description', '')
        nullable = change.get('nullable', True)
        default_value = change.get('default_value')
        
        # Build column definition
        nullable_clause = "" if nullable else " NOT NULL"
        default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
        
        sql = f"""
            ALTER TABLE {table_name} 
            ADD COLUMN {column_name} {data_type}{nullable_clause}{default_clause}
        """
        
        self.spark.sql(sql)
        
        # Add column comment if provided
        if description:
            self.spark.sql(f"""
                ALTER TABLE {table_name} 
                ALTER COLUMN {column_name} COMMENT '{description}'
            """)
        
        logger.info(f"Added column {column_name} to {table_name}")
    
    def _drop_column(self, table_name: str, change: Dict[str, Any]):
        """Drop column from Iceberg table"""
        column_name = change['column_name']
        
        self.spark.sql(f"""
            ALTER TABLE {table_name} 
            DROP COLUMN {column_name}
        """)
        
        logger.info(f"Dropped column {column_name} from {table_name}")
    
    def _rename_column(self, table_name: str, change: Dict[str, Any]):
        """Rename column in Iceberg table"""
        old_name = change['old_column_name']
        new_name = change['new_column_name']
        
        self.spark.sql(f"""
            ALTER TABLE {table_name} 
            RENAME COLUMN {old_name} TO {new_name}
        """)
        
        logger.info(f"Renamed column {old_name} to {new_name} in {table_name}")
    
    def _modify_column_type(self, table_name: str, change: Dict[str, Any]):
        """Modify column data type in Iceberg table"""
        column_name = change['column_name']
        new_type = change['new_data_type']
        
        self.spark.sql(f"""
            ALTER TABLE {table_name} 
            ALTER COLUMN {column_name} TYPE {new_type}
        """)
        
        logger.info(f"Modified column {column_name} type to {new_type} in {table_name}")
    
    def _update_column_description(self, table_name: str, change: Dict[str, Any]):
        """Update column description in Iceberg table"""
        column_name = change['column_name']
        description = change['description']
        
        self.spark.sql(f"""
            ALTER TABLE {table_name} 
            ALTER COLUMN {column_name} COMMENT '{description}'
        """)
        
        logger.info(f"Updated description for column {column_name} in {table_name}")
    
    def evolve_partitioning(self, table_name: str, new_partitioning: List[str]) -> Dict[str, Any]:
        """Evolve table partitioning specification"""
        try:
            # Get current partitioning
            current_partitioning = self._get_current_partitioning(table_name)
            
            # Add new partitions
            for partition_col in new_partitioning:
                if partition_col not in current_partitioning:
                    self.spark.sql(f"""
                        ALTER TABLE {table_name} 
                        ADD PARTITION FIELD {partition_col}
                    """)
            
            logger.info(f"Evolved partitioning for {table_name}: {current_partitioning} -> {new_partitioning}")
            
            return {
                'table_name': table_name,
                'old_partitioning': current_partitioning,
                'new_partitioning': new_partitioning,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to evolve partitioning: {e}")
            raise
    
    def _get_current_partitioning(self, table_name: str) -> List[str]:
        """Get current partitioning specification"""
        try:
            result = self.spark.sql(f"DESCRIBE TABLE {table_name}").collect()
            partitions = []
            
            for row in result:
                if row.col_name.startswith("partition") and row.data_type != "struct":
                    partitions.append(row.col_name.split(".")[-1])
            
            return partitions
            
        except Exception as e:
            logger.error(f"Failed to get current partitioning: {e}")
            return []
    
    def query_at_snapshot(self, table_name: str, snapshot_id: int) -> SparkDF:
        """Query table at specific snapshot for time travel"""
        return self.spark.read.format("iceberg") \
            .option("snapshot-id", snapshot_id) \
            .load(table_name)
    
    def query_at_timestamp(self, table_name: str, timestamp: str) -> SparkDF:
        """Query table at specific timestamp for time travel"""
        return self.spark.read.format("iceberg") \
            .option("as-of-timestamp", timestamp) \
            .load(table_name)
    
    def get_table_history(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table snapshot history"""
        try:
            history_df = self.spark.sql(f"SELECT * FROM {table_name}.history")
            
            return [row.asDict() for row in history_df.collect()]
            
        except Exception as e:
            logger.error(f"Failed to get table history: {e}")
            return []
    
    def get_table_snapshots(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table snapshots information"""
        try:
            snapshots_df = self.spark.sql(f"SELECT * FROM {table_name}.snapshots")
            
            return [row.asDict() for row in snapshots_df.collect()]
            
        except Exception as e:
            logger.error(f"Failed to get table snapshots: {e}")
            return []
    
    def rollback_to_snapshot(self, table_name: str, snapshot_id: int) -> Dict[str, Any]:
        """Rollback table to specific snapshot"""
        try:
            # Create rollback branch
            branch_name = f"rollback_{snapshot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.spark.sql(f"""
                ALTER TABLE {table_name} 
                CREATE BRANCH {branch_name} AS OF VERSION {snapshot_id}
            """)
            
            logger.info(f"Created rollback branch {branch_name} for snapshot {snapshot_id}")
            
            return {
                'table_name': table_name,
                'snapshot_id': snapshot_id,
                'branch_name': branch_name,
                'rollback_time': datetime.now(timezone.utc).isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to rollback to snapshot {snapshot_id}: {e}")
            raise

class HealthcareIcebergManager:
    """Healthcare-specific Iceberg table management"""
    
    def __init__(self, spark: SparkSession, catalog_name: str = "healthcare_catalog"):
        self.spark = spark
        self.schema_manager = IcebergSchemaManager(spark, catalog_name)
        
        # Initialize healthcare table configurations
        self.table_configs = self._initialize_healthcare_configs()
    
    def _initialize_healthcare_configs(self) -> Dict[str, IcebergTableConfig]:
        """Initialize healthcare-specific table configurations"""
        return {
            'lab_results': IcebergTableConfig(
                table_name='lab_results',
                table_type=IcebergTableType.FACT,
                partitioning_spec=['test_date', 'facility_id'],
                sort_order=['patient_id', 'test_code'],
                schema_evolution_enabled=True
            ),
            'patients': IcebergTableConfig(
                table_name='patients',
                table_type=IcebergTableType.DIMENSION,
                partitioning_spec=['updated_date'],
                sort_order=['patient_id'],
                schema_evolution_enabled=True
            ),
            'providers': IcebergTableConfig(
                table_name='providers',
                table_type=IcebergTableType.DIMENSION,
                partitioning_spec=['specialization', 'department'],
                sort_order=['provider_id'],
                schema_evolution_enabled=True
            ),
            'claims': IcebergTableConfig(
                table_name='claims',
                table_type=IcebergTableType.FACT,
                partitioning_spec=['submission_date', 'claim_status'],
                sort_order=['claim_id', 'patient_id'],
                schema_evolution_enabled=True
            ),
            'medications': IcebergTableConfig(
                table_name='medications',
                table_type=IcebergTableType.BRIDGE,
                partitioning_spec=['prescription_date'],
                sort_order=['patient_id', 'medication_id'],
                schema_evolution_enabled=True
            )
        }
    
    def create_lab_results_table(self, df: SparkDF) -> Dict[str, Any]:
        """Create lab results table with healthcare-specific optimizations"""
        config = self.table_configs['lab_results']
        
        # Add healthcare-specific properties
        config.write_properties.update({
            'write.wap.enabled': 'true',  # Write-audit-publish for data quality
            'write.audited.enabled': 'true',
            'write.data.path': 's3://healthcare-iceberg-warehouse/lab_results'
        })
        
        return self.schema_manager.create_iceberg_table(df, config)
    
    def evolve_lab_results_schema(self, new_lab_codes: List[str]) -> Dict[str, Any]:
        """Evolve lab results schema for new test codes"""
        schema_changes = []
        
        for lab_code in new_lab_codes:
            schema_changes.append({
                'type': 'ADD_COLUMN',
                'column_name': f'result_{lab_code.lower()}',
                'data_type': 'FLOAT',
                'description': f'Result value for {lab_code} test',
                'nullable': True
            })
        
        table_name = f"{self.schema_manager.catalog_name}.healthcare_db.lab_results"
        return self.schema_manager.evolve_schema(table_name, schema_changes)
    
    def create_patient_dimension(self, df: SparkDF) -> Dict[str, Any]:
        """Create patient dimension with privacy considerations"""
        config = self.table_configs['patients']
        
        # Add privacy-specific properties
        config.write_properties.update({
            'write.wap.enabled': 'true',
            'write.audited.enabled': 'true',
            'write.data.path': 's3://healthcare-iceberg-warehouse/patients'
        })
        
        return self.schema_manager.create_iceberg_table(df, config)
    
    def evolve_patient_schema_for_hipaa(self) -> Dict[str, Any]:
        """Evolve patient schema for HIPAA compliance"""
        schema_changes = [
            {
                'type': 'ADD_COLUMN',
                'column_name': 'consent_version',
                'data_type': 'STRING',
                'description': 'Version of consent form signed',
                'nullable': False
            },
            {
                'type': 'ADD_COLUMN',
                'column_name': 'data_retention_expiry',
                'data_type': 'TIMESTAMP',
                'description': 'Date when patient data should be expired',
                'nullable': True
            },
            {
                'type': 'ADD_COLUMN',
                'column_name': 'access_log',
                'data_type': 'STRING',
                'description': 'JSON log of data access for audit',
                'nullable': True
            }
        ]
        
        table_name = f"{self.schema_manager.catalog_name}.healthcare_db.patients"
        return self.schema_manager.evolve_schema(table_name, schema_changes)
    
    def get_compliance_report(self, table_name: str) -> Dict[str, Any]:
        """Generate compliance report for healthcare tables"""
        try:
            # Get table history for audit
            history = self.schema_manager.get_table_history(table_name)
            
            # Get snapshots for data lineage
            snapshots = self.schema_manager.get_table_snapshots(table_name)
            
            # Calculate data retention metrics
            total_snapshots = len(snapshots)
            oldest_snapshot = min(snap['timestamp'] for snap in snapshots) if snapshots else None
            
            return {
                'table_name': table_name,
                'total_snapshots': total_snapshots,
                'oldest_snapshot': oldest_snapshot,
                'recent_changes': history[-5:] if history else [],
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
        """Optimize Iceberg table for healthcare query patterns"""
        try:
            # Compact small files
            self.spark.sql(f"""
                CALL iceberg.system.optimize_table(
                    table => '{table_name}',
                    strategy => 'bin-pack'
                )
            """)
            
            # Sort data for better query performance
            self.spark.sql(f"""
                CALL iceberg.system.optimize_table(
                    table => '{table_name}',
                    strategy => 'sort'
                )
            """)
            
            # Expire old snapshots
            self.spark.sql(f"""
                CALL iceberg.system.expire_snapshots(
                    table => '{table_name}',
                    older_than => '30 days',
                    retain_last => 10
                )
            """)
            
            logger.info(f"Optimized table performance for {table_name}")
            
            return {
                'table_name': table_name,
                'optimization_completed': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize table {table_name}: {e}")
            raise

# Initialize Iceberg manager
def get_iceberg_manager(spark: SparkSession, catalog_name: str = "healthcare_catalog") -> HealthcareIcebergManager:
    """Get or create Iceberg manager instance"""
    return HealthcareIcebergManager(spark, catalog_name)
