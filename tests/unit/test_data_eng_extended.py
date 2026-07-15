import importlib
import sys
import types
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

def mock_dependencies():
    pyspark = types.ModuleType("pyspark")
    pyspark_sql = types.ModuleType("pyspark.sql")
    pyspark_functions = types.ModuleType("pyspark.sql.functions")
    pyspark_types = types.ModuleType("pyspark.sql.types")
    redis_module = types.ModuleType("redis")

    class SparkSession:
        pass
    class SparkDF:
        pass
    class Redis:
        pass
    class _SparkType:
        def __init__(self, *args, **kwargs):
            pass

    def _function_stub(*args, **kwargs):
        return None

    pyspark_sql.SparkSession = SparkSession
    pyspark_sql.DataFrame = SparkDF
    for name in ["col", "count", "sum", "avg", "max", "min"]:
        setattr(pyspark_functions, name, _function_stub)
    for name in ["StructType", "StructField", "StringType", "FloatType", "DateType", "TimestampType"]:
        setattr(pyspark_types, name, _SparkType)
    
    redis_module.Redis = Redis

    sys.modules["pyspark"] = pyspark
    sys.modules["pyspark.sql"] = pyspark_sql
    sys.modules["pyspark.sql.functions"] = pyspark_functions
    sys.modules["pyspark.sql.types"] = pyspark_types
    sys.modules["redis"] = redis_module

mock_dependencies()

from backend.data_engineering_platform import (
    HealthcareDataPipeline,
    PIPELINE_FAILURE_MESSAGE,
    DataQualityMetrics,
)

class MockSparkSession:
    def __init__(self):
        self.read = MockSparkReader()

class MockSparkReader:
    def format(self, fmt):
        return self
    def options(self, **kwargs):
        return self
    def load(self):
        return MockDataFrame()
    def json(self, path):
        return MockDataFrame()

class MockDataFrame:
    def __init__(self, count_val=10):
        self._count = count_val
        self.columns = ["patient_id", "value"]
        self.schema = MagicMock()
        self.schema.fields = [MagicMock(name="patient_id")]
    
    def count(self):
        return self._count
        
    def dropDuplicates(self):
        return self
        
    def fillna(self, value):
        return self
        
    def write(self):
        return MockSparkWriter()
        
    def agg(self, *args, **kwargs):
        mock_row = MagicMock()
        mock_row.asDict.return_value = {"completeness": 0.99, "count": 100}
        
        # Make the returned object have collect() method that returns [mock_row]
        result = MagicMock()
        result.collect.return_value = [mock_row]
        return result

class MockSparkWriter:
    def format(self, fmt):
        return self
    def options(self, **kwargs):
        return self
    def mode(self, m):
        return self
    def save(self):
        pass

@pytest.fixture
def data_pipeline():
    spark = MockSparkSession()
    redis = MagicMock()
    db = MagicMock()
    return HealthcareDataPipeline(spark, redis, db)

@pytest.mark.asyncio
async def test_extract_database(data_pipeline):
    config = {
        "type": "database",
        "connection_string": "jdbc:postgres://localhost/db",
        "query": "SELECT * FROM patients",
        "incremental_column": "updated_at",
        "last_extract_value": "2024-01-01"
    }
    result = await data_pipeline._extract_from_database(config)
    assert result["status"] == "success"
    assert result["record_count"] == 10

@pytest.mark.asyncio
async def test_extract_api(data_pipeline):
    config = {
        "type": "api",
        "endpoint": "https://api.example.com/data",
        "auth_token": "secret"
    }
    with patch("httpx.AsyncClient") as mock_client:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"id": 1}, {"id": 2}]
        
        instance = AsyncMock()
        instance.get.return_value = mock_resp
        instance.__aenter__.return_value = instance
        mock_client.return_value = instance
        
        result = await data_pipeline._extract_from_api(config)
        assert result["status"] == "success"
        assert result["record_count"] == 2

@pytest.mark.asyncio
async def test_extract_file(data_pipeline):
    config = {
        "type": "file",
        "file_path": "/data/test.json",
        "format": "json"
    }
    result = await data_pipeline._extract_from_file(config)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_extract_stream(data_pipeline):
    config = {
        "type": "stream",
        "topic": "test_topic",
        "brokers": "localhost:9092"
    }
    result = await data_pipeline._extract_from_stream(config)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_transform_data(data_pipeline):
    extract_result = {"source_1": {"data": MockDataFrame(), "format": "spark_df"}}
    config = {
        "transformations": [
            {"type": "clean_nulls"},
            {"type": "deduplicate"}
        ]
    }
    result = await data_pipeline._transform_data(extract_result, config)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_load_data(data_pipeline):
    transform_result = {"transformed_data": MockDataFrame()}
    config = {
        "target": {
            "type": "database",
            "connection_string": "jdbc:postgres://localhost/db",
            "table": "target_table",
            "mode": "append"
        }
    }
    result = await data_pipeline._load_data(transform_result, config)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_assess_data_quality(data_pipeline):
    load_result = {"data": MockDataFrame()}
    metrics = await data_pipeline._assess_data_quality(load_result)
    assert isinstance(metrics, DataQualityMetrics)

@pytest.mark.asyncio
async def test_run_etl_pipeline(data_pipeline):
    config = {
        "pipeline_id": "test_pipe_1",
        "sources": [
            {"name": "s1", "type": "database", "connection_string": "jdbc:", "query": "select 1"}
        ],
        "transformations": [],
        "target": {"type": "database", "connection_string": "jdbc:", "table": "t1", "mode": "append"}
    }
    result = await data_pipeline.run_etl_pipeline(config)
    assert result["status"] == "success"
    assert result["pipeline_id"] == "test_pipe_1"

@pytest.mark.asyncio
async def test_cache_pipeline_metrics(data_pipeline):
    metrics = {"status": "success", "record_count": 100}
    await data_pipeline._cache_pipeline_metrics(metrics)
    assert data_pipeline.redis.hset.called
