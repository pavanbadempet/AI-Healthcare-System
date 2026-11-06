"""
PySpark Session Factory with Cloud-Native Storage and Catalogs.
Supports AWS S3, Azure ADLS Gen2, Databricks Unity Catalog, and Snowflake.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from pyspark.sql import SparkSession

    SPARK_AVAILABLE = True
except Exception:

    class _DummySparkBuilder:
        @classmethod
        def appName(cls, *args, **kwargs):
            return cls

        @classmethod
        def config(cls, *args, **kwargs):
            return cls

        @classmethod
        def getOrCreate(cls, *args, **kwargs):
            return None

    class _DummySparkSession:
        builder = _DummySparkBuilder

    SparkSession = _DummySparkSession  # type: ignore
    SPARK_AVAILABLE = False


def apply_cloud_integration_configs(builder: Any) -> Any:
    """Apply cloud-specific integrations (AWS, Azure, Databricks, Snowflake)."""
    provider = os.getenv("CLOUD_PROVIDER", "").strip().lower()

    # 1. AWS (S3, EMR, Glue Catalog)
    if provider == "aws" or os.getenv("AWS_ACCESS_KEY_ID"):
        aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        if aws_key and aws_secret:
            builder = (
                builder.config("spark.hadoop.fs.s3a.access.key", aws_key)
                .config("spark.hadoop.fs.s3a.secret.key", aws_secret)
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
                .config(
                    "spark.hadoop.fs.s3a.aws.credentials.provider",
                    "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
                )
            )

        # Enable AWS Glue Data Catalog integration if explicitly requested
        if os.getenv("AWS_GLUE_CATALOG_ENABLED", "").strip().lower() in ("1", "true", "yes"):
            builder = builder.config(
                "hive.metastore.client.factory.class",
                "com.amazonaws.glue.catalog.metastore.AWSGlueClientMetastoreFactory",
            )

    # 2. Microsoft Azure (ADLS Gen2 / Blob Storage)
    if provider == "azure" or os.getenv("AZURE_STORAGE_ACCOUNT"):
        account = os.getenv("AZURE_STORAGE_ACCOUNT")
        key = os.getenv("AZURE_STORAGE_KEY")
        if account and key:
            builder = builder.config(f"fs.azure.account.key.{account}.dfs.core.windows.net", key).config(
                "fs.azure.impl", "org.apache.hadoop.fs.azurebfs.SecureAzureBlobFileSystem"
            )

    # 3. Databricks Unity Catalog
    if provider == "databricks" or os.getenv("DATABRICKS_HOST"):
        db_host = os.getenv("DATABRICKS_HOST")
        db_token = os.getenv("DATABRICKS_TOKEN")
        if db_host and db_token:
            builder = (
                builder.config("spark.sql.catalog.uc", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
                .config("spark.sql.catalog.uc.type", "unity")
                .config("spark.databricks.service.address", db_host)
                .config("spark.databricks.service.token", db_token)
            )

    # 4. Snowflake Spark Connector
    if provider == "snowflake" or os.getenv("SNOWFLAKE_URL"):
        sf_url = os.getenv("SNOWFLAKE_URL")
        sf_user = os.getenv("SNOWFLAKE_USER")
        sf_password = os.getenv("SNOWFLAKE_PASSWORD")
        if sf_url and sf_user:
            builder = (
                builder.config("spark.snowflake.url", sf_url)
                .config("spark.snowflake.user", sf_user)
                .config("spark.snowflake.password", sf_password or "")
                .config("spark.snowflake.db", os.getenv("SNOWFLAKE_DATABASE", ""))
                .config("spark.snowflake.schema", os.getenv("SNOWFLAKE_SCHEMA", ""))
            )

    return builder


def create_spark_session() -> Optional[Any]:
    """Create optimized Spark session for healthcare data processing."""
    if not SPARK_AVAILABLE:
        logger.warning("PySpark is not installed. Returning None for spark session.")
        return None

    builder = SparkSession.builder.appName("HealthcareDataPipeline")
    builder = apply_cloud_integration_configs(builder)

    is_hf = bool(
        os.getenv("SPACE_ID") or os.getenv("SPACE_NAME") or os.getenv("HF_SPACE") or os.getenv("RUNNING_IN_HF_SPACE")
    )
    if is_hf:
        builder = (
            builder.config("spark.driver.memory", "512m")
            .config("spark.executor.memory", "512m")
            .config("spark.driver.cores", "1")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.default.parallelism", "2")
            .config("spark.driver.extraJavaOptions", "-XX:+UseG1GC")
        )
    else:
        builder = builder.config("spark.sql.shuffle.partitions", "200")

    return (
        builder.config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .config("spark.sql.ansi.enabled", "true")
        .config("spark.sql.execution.pythonUDF.arrow.enabled", "true")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.json.enableVariantType", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.inMemoryColumnarStorage.compressed", "true")
        .config("spark.sql.inMemoryColumnarStorage.columnBatchSize", "10000")
        .config("spark.sql.autoBroadcastJoinThreshold", "10MB")
        .getOrCreate()
    )
