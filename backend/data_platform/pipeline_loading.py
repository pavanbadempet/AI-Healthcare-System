"""
Pipeline Loading Mixin.
Handles parallel writes to relational databases (JDBC with micro-batching),
files (Parquet, CSV, JSON), cloud data lakes (Delta Lake, S3, ADLS),
and data warehouses (Snowflake, BigQuery, Redshift).
"""

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)
PIPELINE_FAILURE_MESSAGE = "Data pipeline failed. Please review operational logs."

try:
    from pyspark.sql import DataFrame as SparkDF
except Exception:
    SparkDF = Any  # type: ignore


class PipelineLoadingMixin:
    """Loading methods for HealthcareDataPipeline."""

    async def _load_data(self, transform_results: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Load transformed data to target systems."""
        targets = config.get("targets", [])
        load_results = {}

        load_tasks = []
        for target in targets:
            task = self._load_to_target(transform_results, target)
            load_tasks.append(task)

        results = await asyncio.gather(*load_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            target_name = targets[i].get("name", f"target_{i}")
            if isinstance(result, Exception):
                load_results[target_name] = {"error": PIPELINE_FAILURE_MESSAGE}
            else:
                load_results[target_name] = result

        return load_results

    async def _load_to_target(self, transform_results: Dict[str, Any], target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load data to specific target."""
        target_type = target_config.get("type")

        if "merged_dataframe" in transform_results:
            df = transform_results["merged_dataframe"]
        elif "transformed_dataframes" in transform_results:
            df = list(transform_results["transformed_dataframes"].values())[0]
        else:
            raise ValueError("No DataFrame found to load")

        if target_type == "database":
            return await self._load_to_database(df, target_config)
        elif target_type == "file":
            return await self._load_to_file(df, target_config)
        elif target_type == "data_lake":
            return await self._load_to_data_lake(df, target_config)
        elif target_type == "warehouse":
            return await self._load_to_warehouse(df, target_config)
        else:
            raise ValueError(f"Unsupported target type: {target_type}")

    async def _load_to_database(self, df: SparkDF, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load DataFrame to database with batch processing."""
        connection_string = config.get("connection_string")
        table_name = config.get("table_name")
        write_mode = config.get("write_mode", "append")
        batch_size = config.get("batch_size", 10000)

        is_streaming = False
        try:
            is_streaming = df.isStreaming
        except Exception:
            pass

        if is_streaming:
            try:

                def write_micro_batch(micro_df, batch_id):
                    micro_df.write.format("jdbc").options(
                        url=connection_string,
                        driver="org.postgresql.Driver",
                        dbtable=table_name,
                        mode=write_mode,
                        batchsize=batch_size,
                    ).save()

                query = df.writeStream.foreachBatch(write_micro_batch).start()
                query.awaitTermination(timeout=3)

                return {
                    "target": "database",
                    "table": table_name,
                    "is_streaming": True,
                    "message": "Structured streaming query started via foreachBatch micro-batch writer.",
                }
            except Exception as e:
                logger.error("Structured streaming load to database failed: %s", e)
                raise

        try:
            df.write.format("jdbc").options(
                url=connection_string,
                driver="org.postgresql.Driver",
                dbtable=table_name,
                mode=write_mode,
                batchsize=batch_size,
            ).save()

            return {
                "target": "database",
                "table": table_name,
                "records_written": df.count(),
                "write_mode": write_mode,
            }
        except Exception:
            logger.error("Database load failed")
            raise

    async def _load_to_file(self, df: SparkDF, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load DataFrame to file."""
        file_path = config.get("file_path")
        file_format = config.get("format", "parquet")
        write_mode = config.get("write_mode", "overwrite")
        partition_by = config.get("partition_by")

        is_streaming = False
        try:
            is_streaming = df.isStreaming
        except Exception:
            pass

        if is_streaming:
            try:

                def write_micro_batch(micro_df, batch_id):
                    writer = micro_df.write.mode(write_mode)
                    if partition_by:
                        writer = writer.partitionBy(partition_by)
                    if file_format == "parquet":
                        writer.parquet(file_path)
                    elif file_format == "csv":
                        writer.option("header", "true").csv(file_path)
                    elif file_format == "json":
                        writer.json(file_path)

                query = df.writeStream.foreachBatch(write_micro_batch).start()
                query.awaitTermination(timeout=3)

                return {
                    "target": "file",
                    "file_path": file_path,
                    "format": file_format,
                    "is_streaming": True,
                    "message": "Structured streaming query started via foreachBatch file writer.",
                }
            except Exception as e:
                logger.error("Structured streaming load to file failed: %s", e)
                raise

        try:
            writer = df.write.mode(write_mode)
            if partition_by:
                writer = writer.partitionBy(partition_by)

            if file_format == "parquet":
                writer.parquet(file_path)
            elif file_format == "csv":
                writer.option("header", "true").csv(file_path)
            elif file_format == "json":
                writer.json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            return {
                "target": "file",
                "file_path": file_path,
                "format": file_format,
                "records_written": df.count(),
            }
        except Exception:
            logger.error("File load failed")
            raise

    async def _load_to_data_lake(self, df: SparkDF, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load DataFrame to data lake (S3, ADLS, GCS)."""
        storage_path = config.get("storage_path")
        file_format = config.get("format", "parquet")
        partition_by = config.get("partition_by")

        try:
            writer = df.write.mode("overwrite")
            if partition_by:
                writer = writer.partitionBy(partition_by)

            if file_format == "parquet":
                writer.parquet(storage_path)
            elif file_format == "delta":
                writer.format("delta").save(storage_path)
            else:
                raise ValueError(f"Unsupported data lake format: {file_format}")

            return {
                "target": "data_lake",
                "storage_path": storage_path,
                "format": file_format,
                "records_written": df.count(),
            }
        except Exception:
            logger.error("Data lake load failed")
            raise

    async def _load_to_warehouse(self, df: SparkDF, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load DataFrame to data warehouse (Snowflake, BigQuery, Redshift)."""
        warehouse_type = config.get("warehouse_type")

        if warehouse_type == "snowflake":
            return await self._load_to_snowflake(df, config)
        elif warehouse_type == "bigquery":
            return await self._load_to_bigquery(df, config)
        elif warehouse_type == "redshift":
            return await self._load_to_redshift(df, config)
        else:
            raise ValueError(f"Unsupported warehouse type: {warehouse_type}")
