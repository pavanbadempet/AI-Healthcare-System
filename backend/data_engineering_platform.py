"""
Data Engineering Platform - Healthcare Analytics.

Core focus: Scalable data pipelines, ETL/ELT, and big data processing.
Decomposed into clean modular components in backend.data_platform:
- Extraction: backend.data_platform.pipeline_extraction
- Transformation: backend.data_platform.pipeline_transformation
- Loading: backend.data_platform.pipeline_loading
- Quality: backend.data_platform.pipeline_quality
- Spark Engine: backend.data_platform.spark_session
- Router: backend.data_platform.router
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import redis

from backend.data_platform.pipeline_extraction import (
    PIPELINE_FAILURE_MESSAGE,
    SQL_IDENTIFIER_RE,
    PipelineExtractionMixin,
    _append_incremental_filter,
    _sql_literal,
    _validate_api_base_url,
)
from backend.data_platform.pipeline_loading import PipelineLoadingMixin
from backend.data_platform.pipeline_quality import (
    DataQualityMetrics,
    PipelineQualityMixin,
)
from backend.data_platform.pipeline_transformation import PipelineTransformationMixin
from backend.data_platform.router import (
    AdaptiveDataPlatformRouter,
    DataScaleEngine,
)
from backend.data_platform.spark_session import (
    SPARK_AVAILABLE,
    create_spark_session,
)
from backend.data_platform.spark_session import (
    apply_cloud_integration_configs as _apply_cloud_integration_configs,
)

try:
    from pyspark.sql import DataFrame as SparkDF
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (
        DateType,
        FloatType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )
except Exception:
    SparkDF = Any  # type: ignore
    SparkSession = Any  # type: ignore
    DateType = FloatType = StringType = StructField = StructType = TimestampType = Any  # type: ignore

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class DataPipeline:
    """Data pipeline configuration and metadata."""

    pipeline_id: str
    name: str
    source_system: str
    target_system: str
    schedule: str
    status: PipelineStatus
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    records_processed: int
    error_count: int
    avg_duration_seconds: float
    data_quality_score: float


class HealthcareDataPipeline(
    PipelineExtractionMixin,
    PipelineTransformationMixin,
    PipelineLoadingMixin,
    PipelineQualityMixin,
):
    """Enterprise-grade healthcare data processing platform."""

    def __init__(self, spark_session: SparkSession, redis_client: redis.Redis, db_session):
        self.spark = spark_session
        self.redis = redis_client
        self.db = db_session
        self.executor = ThreadPoolExecutor(max_workers=8)

        # Initialize data schemas
        if SPARK_AVAILABLE and StructType is not Any:
            self.patient_schema = StructType(
                [
                    StructField("patient_id", StringType(), False),
                    StructField("medical_record_number", StringType(), False),
                    StructField("first_name", StringType(), True),
                    StructField("last_name", StringType(), True),
                    StructField("date_of_birth", DateType(), True),
                    StructField("gender", StringType(), True),
                    StructField("email", StringType(), True),
                    StructField("phone", StringType(), True),
                    StructField("address", StringType(), True),
                    StructField("insurance_id", StringType(), True),
                    StructField("primary_care_physician", StringType(), True),
                    StructField("created_at", TimestampType(), False),
                    StructField("updated_at", TimestampType(), False),
                ]
            )

            self.lab_results_schema = StructType(
                [
                    StructField("result_id", StringType(), False),
                    StructField("patient_id", StringType(), False),
                    StructField("test_code", StringType(), False),
                    StructField("test_name", StringType(), True),
                    StructField("result_value", FloatType(), True),
                    StructField("result_unit", StringType(), True),
                    StructField("reference_range", StringType(), True),
                    StructField("abnormal_flag", StringType(), True),
                    StructField("test_date", TimestampType(), False),
                    StructField("performed_by", StringType(), True),
                    StructField("facility_id", StringType(), True),
                    StructField("created_at", TimestampType(), False),
                ]
            )

            self.claims_schema = StructType(
                [
                    StructField("claim_id", StringType(), False),
                    StructField("patient_id", StringType(), False),
                    StructField("provider_id", StringType(), False),
                    StructField("service_date", DateType(), True),
                    StructField("procedure_code", StringType(), False),
                    StructField("diagnosis_code", StringType(), True),
                    StructField("billed_amount", FloatType(), False),
                    StructField("allowed_amount", FloatType(), True),
                    StructField("paid_amount", FloatType(), True),
                    StructField("claim_status", StringType(), False),
                    StructField("submission_date", TimestampType(), False),
                    StructField("processing_date", TimestampType(), True),
                ]
            )
        else:
            self.patient_schema = None
            self.lab_results_schema = None
            self.claims_schema = None

    async def run_etl_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive ETL pipeline with data quality checks."""
        start_time = time.time()
        pipeline_id = pipeline_config.get("pipeline_id", f"pipeline_{int(time.time())}")

        try:
            # Extract phase
            extract_result = await self._extract_data(pipeline_config)

            # Transform phase
            transform_result = await self._transform_data(extract_result, pipeline_config)

            # Load phase
            load_result = await self._load_data(transform_result, pipeline_config)

            # Get the Spark DataFrame that was processed
            df_to_assess = None
            if "merged_dataframe" in transform_result:
                df_to_assess = transform_result["merged_dataframe"]
            elif "transformed_dataframes" in transform_result and transform_result["transformed_dataframes"]:
                df_to_assess = list(transform_result["transformed_dataframes"].values())[0]

            # Data quality assessment
            quality_metrics = await self._assess_data_quality(load_result, df=df_to_assess)

            # Performance metrics
            duration = time.time() - start_time
            record_count = load_result.get("record_count", 0)
            performance_metrics = {
                "pipeline_id": pipeline_id,
                "duration_seconds": duration,
                "records_processed": record_count,
                "throughput_records_per_second": record_count / duration if duration > 0 else 0,
                "data_quality_score": quality_metrics.overall_score,
                "status": "completed",
            }

            # Cache metrics for monitoring
            await self._cache_pipeline_metrics(performance_metrics)

            return {
                "status": "success",
                "pipeline_id": pipeline_id,
                "metrics": performance_metrics,
                "data_quality": quality_metrics.__dict__,
                "extract_result": extract_result,
                "transform_result": transform_result,
                "load_result": load_result,
            }

        except Exception:
            logger.error("ETL pipeline failed")
            return {
                "status": "failed",
                "pipeline_id": pipeline_id,
                "error": PIPELINE_FAILURE_MESSAGE,
                "duration_seconds": time.time() - start_time,
            }


# Global pipeline instance
data_pipeline: Optional[HealthcareDataPipeline] = None


def get_data_pipeline(spark_session: SparkSession, redis_client: redis.Redis, db_session) -> HealthcareDataPipeline:
    """Get or create data pipeline singleton instance."""
    global data_pipeline
    if data_pipeline is None:
        data_pipeline = HealthcareDataPipeline(spark_session, redis_client, db_session)
    return data_pipeline


__all__ = [
    "AdaptiveDataPlatformRouter",
    "DataPipeline",
    "DataQualityMetrics",
    "DataScaleEngine",
    "HealthcareDataPipeline",
    "PIPELINE_FAILURE_MESSAGE",
    "PipelineStatus",
    "SPARK_AVAILABLE",
    "SQL_IDENTIFIER_RE",
    "SparkDF",
    "SparkSession",
    "_append_incremental_filter",
    "_apply_cloud_integration_configs",
    "_sql_literal",
    "_validate_api_base_url",
    "create_spark_session",
    "data_pipeline",
    "get_data_pipeline",
]
