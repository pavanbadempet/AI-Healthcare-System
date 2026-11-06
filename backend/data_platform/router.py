"""
Adaptive Data Platform Router.
Dynamically routes analytical and Medallion Lakehouse workloads based on dataset volume:
- Small/Edge Scale (<50GB / Single Node): DuckDB + Polars (Embedded in-memory, instant response, zero cluster overhead)
- Enterprise Large Scale (>50GB / Petabytes / Multi-Node Cluster): Apache PySpark + Delta Lake (Distributed execution)
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DataScaleEngine(Enum):
    DUCKDB_EMBEDDED = "duckdb_embedded"
    PYSPARK_DISTRIBUTED = "pyspark_distributed"


class AdaptiveDataPlatformRouter:
    """Scale-aware Data Platform Router."""

    LARGE_SCALE_THRESHOLD_BYTES = 50 * 1024 * 1024 * 1024  # 50 GB threshold

    def __init__(self, preferred_mode: Optional[str] = None):
        self.preferred_mode = (preferred_mode or os.getenv("SCALE_MODE", "auto")).lower()

    def determine_engine(self, dataset_path_or_bytes: Optional[Any] = None) -> DataScaleEngine:
        """Determines the appropriate engine based on scale requirements."""
        if self.preferred_mode in ("embedded", "duckdb"):
            return DataScaleEngine.DUCKDB_EMBEDDED
        if self.preferred_mode in ("distributed", "pyspark"):
            return DataScaleEngine.PYSPARK_DISTRIBUTED

        if isinstance(dataset_path_or_bytes, (int, float)):
            if dataset_path_or_bytes >= self.LARGE_SCALE_THRESHOLD_BYTES:
                return DataScaleEngine.PYSPARK_DISTRIBUTED
        elif isinstance(dataset_path_or_bytes, str) and os.path.exists(dataset_path_or_bytes):
            total_size = 0
            if os.path.isfile(dataset_path_or_bytes):
                total_size = os.path.getsize(dataset_path_or_bytes)
            else:
                for root, _, files in os.walk(dataset_path_or_bytes):
                    for f in files:
                        total_size += os.path.getsize(os.path.join(root, f))
            if total_size >= self.LARGE_SCALE_THRESHOLD_BYTES:
                return DataScaleEngine.PYSPARK_DISTRIBUTED

        return DataScaleEngine.DUCKDB_EMBEDDED

    def execute_medallion_pipeline(
        self,
        bronze_path: str,
        silver_path: str,
        gold_path: str,
        spark_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Executes Medallion Lakehouse pipeline using the scale-optimal engine."""
        engine = self.determine_engine(bronze_path)
        logger.info("Executing Medallion Lakehouse pipeline using engine: %s", engine.value)

        if engine == DataScaleEngine.DUCKDB_EMBEDDED:
            from backend.duckdb_client import get_duckdb_client

            client = get_duckdb_client()
            res = client.process_embedded_medallion_stream(bronze_path, silver_path, gold_path)
            res["executed_engine"] = "DuckDB (Embedded Edge Scale)"
            return res
        else:
            if spark_session is None:
                from backend.data_platform.spark_session import create_spark_session

                spark_session = create_spark_session()

            from pyspark.sql.functions import avg, count
            from pyspark.sql.functions import max as spark_max

            from backend.data_platform.lakeflow import MedFlowPipeline

            pipe = MedFlowPipeline("medallion_lakehouse_pipeline", spark=spark_session)
            pipe.add_source("bronze_source", lambda: spark_session.read.format("delta").load(bronze_path))
            pipe.add_transform(
                "silver_filter",
                lambda df: df.filter("heart_rate BETWEEN 30 AND 220 AND spo2 BETWEEN 50 AND 100"),
            )
            pipe.add_transform(
                "silver_write",
                lambda df: (df.write.format("delta").mode("append").save(silver_path), df)[1],
            )
            pipe.add_transform(
                "gold_aggregate",
                lambda df: df.groupBy("patient_id").agg(
                    avg("heart_rate").alias("avg_heart_rate"),
                    avg("spo2").alias("avg_spo2"),
                    count("*").alias("vital_sample_count"),
                    spark_max("timestamp").alias("last_updated"),
                ),
            )

            def _gold_sink(df):
                df.write.format("delta").mode("overwrite").save(gold_path)
                return df.count()

            pipe.add_sink("gold_write_sink", _gold_sink)
            run_result = pipe.execute()

            return {
                "status": "success" if run_result.status == "COMPLETED" else "failed",
                "gold_records": run_result.total_records_processed,
                "executed_engine": "MedFlow Declarative PySpark + Delta Lake (Distributed Large Scale)",
                "pipeline_run": run_result.model_dump(),
            }
