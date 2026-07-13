import importlib
import sys
import types

import pytest


def _load_data_engineering_platform(monkeypatch):
    for module_name in [
        "backend.data_engineering_platform",
        "pyspark",
        "pyspark.sql",
        "pyspark.sql.functions",
        "pyspark.sql.types",
        "redis",
    ]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

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

    monkeypatch.setitem(sys.modules, "pyspark", pyspark)
    monkeypatch.setitem(sys.modules, "pyspark.sql", pyspark_sql)
    monkeypatch.setitem(sys.modules, "pyspark.sql.functions", pyspark_functions)
    monkeypatch.setitem(sys.modules, "pyspark.sql.types", pyspark_types)
    monkeypatch.setitem(sys.modules, "redis", redis_module)

    return importlib.import_module("backend.data_engineering_platform")


class _FakeJdbcDataFrame:
    schema = {"fields": []}

    def count(self):
        return 0

    def agg(self, mapping):
        self.agg_mapping = mapping
        return self

    def collect(self):
        return [(None,)]


class _FakeJdbcReader:
    def __init__(self):
        self.options_kwargs = {}

    def format(self, source_format):
        self.source_format = source_format
        return self

    def options(self, **kwargs):
        self.options_kwargs = kwargs
        return self

    def load(self):
        return _FakeJdbcDataFrame()


class _FakeSpark:
    def __init__(self):
        self.read = _FakeJdbcReader()

    def createDataFrame(self, data, schema=None):
        self.created_dataframe = {"data": data, "schema": schema}
        return self.created_dataframe


@pytest.mark.asyncio
async def test_run_etl_pipeline_hides_sensitive_exception_details(monkeypatch, caplog):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=object(),
        redis_client=object(),
        db_session=object(),
    )
    sensitive_error = "jdbc://db password=db-secret patient_name=Sensitive User"

    async def fail_extract(config):
        raise RuntimeError(sensitive_error)

    pipeline._extract_data = fail_extract
    caplog.set_level("ERROR", logger="backend.data_engineering_platform")

    result = await pipeline.run_etl_pipeline({"pipeline_id": "safe-pipeline"})

    assert result["status"] == "failed"
    assert result["error"] == data_engineering_platform.PIPELINE_FAILURE_MESSAGE
    assert sensitive_error not in str(result)
    assert "db-secret" not in str(result)
    assert "Sensitive User" not in str(result)
    assert sensitive_error not in caplog.text
    assert "db-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


@pytest.mark.asyncio
async def test_extract_data_hides_source_exception_details(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=object(),
        redis_client=object(),
        db_session=object(),
    )
    sensitive_error = "api token=extract-secret patient_name=Sensitive User"

    async def fail_extract_from_source(source):
        raise RuntimeError(sensitive_error)

    pipeline._extract_from_source = fail_extract_from_source

    result = await pipeline._extract_data({"sources": [{"name": "ehr_api"}]})

    assert result == {"ehr_api": {"error": data_engineering_platform.PIPELINE_FAILURE_MESSAGE}}
    assert sensitive_error not in str(result)
    assert "extract-secret" not in str(result)
    assert "Sensitive User" not in str(result)


@pytest.mark.asyncio
async def test_database_extract_rejects_unsafe_incremental_column(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=_FakeSpark(),
        redis_client=object(),
        db_session=object(),
    )

    with pytest.raises(ValueError, match="Invalid incremental column"):
        await pipeline._extract_from_database({
            "connection_string": "jdbc:postgresql://db/warehouse",
            "query": "SELECT * FROM vital_observations",
            "incremental_column": "updated_at; DROP TABLE users",
            "last_extract_value": "2026-05-01T00:00:00Z",
        })


@pytest.mark.asyncio
async def test_database_extract_escapes_incremental_value_and_preserves_where(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    fake_spark = _FakeSpark()
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=fake_spark,
        redis_client=object(),
        db_session=object(),
    )

    await pipeline._extract_from_database({
        "connection_string": "jdbc:postgresql://db/warehouse",
        "query": "SELECT * FROM vital_observations WHERE facility_id = 7",
        "incremental_column": "observed_at",
        "last_extract_value": "2026-05-01T00:00:00Z' OR '1'='1",
    })

    assert fake_spark.read.options_kwargs["query"] == (
        "SELECT * FROM vital_observations WHERE facility_id = 7 "
        "AND observed_at > '2026-05-01T00:00:00Z'' OR ''1''=''1'"
    )


@pytest.mark.asyncio
async def test_api_extract_uses_bounded_request_timeout(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    fake_spark = _FakeSpark()
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=fake_spark,
        redis_client=object(),
        db_session=object(),
    )
    calls = []

    class Response:
        status_code = 200

        def json(self):
            return []

    def fake_get(url, headers=None, timeout=None):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return Response()

    monkeypatch.setattr("requests.get", fake_get)

    result = await pipeline._extract_from_api({
        "base_url": "https://ehr.example.test",
        "endpoint": "patients",
        "headers": {"Authorization": "Bearer synthetic-token"},
    })

    assert result["record_count"] == 0
    assert calls == [{
        "url": "https://ehr.example.test/patients?page=1",
        "headers": {"Authorization": "Bearer synthetic-token"},
        "timeout": 30,
    }]


@pytest.mark.asyncio
async def test_api_extract_rejects_unsupported_base_url_scheme(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=_FakeSpark(),
        redis_client=object(),
        db_session=object(),
    )

    def fail_get(*args, **kwargs):
        raise AssertionError("request should not be sent for unsupported API schemes")

    monkeypatch.setattr("requests.get", fail_get)

    with pytest.raises(ValueError, match="API base_url must use http or https"):
        await pipeline._extract_from_api({
            "base_url": "file:///tmp/patients",
            "endpoint": "patients",
        })


@pytest.mark.asyncio
async def test_load_data_hides_target_exception_details(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=object(),
        redis_client=object(),
        db_session=object(),
    )
    sensitive_error = "warehouse password=load-secret patient_name=Sensitive User"

    async def fail_load_to_target(transform_results, target):
        raise RuntimeError(sensitive_error)

    pipeline._load_to_target = fail_load_to_target

    result = await pipeline._load_data({}, {"targets": [{"name": "warehouse"}]})

    assert result == {"warehouse": {"error": data_engineering_platform.PIPELINE_FAILURE_MESSAGE}}
    assert sensitive_error not in str(result)
    assert "load-secret" not in str(result)
    assert "Sensitive User" not in str(result)


@pytest.mark.asyncio
async def test_enrichment_lookup_pandas(monkeypatch):
    data_engineering_platform = _load_data_engineering_platform(monkeypatch)
    pipeline = data_engineering_platform.HealthcareDataPipeline(
        spark_session=object(),
        redis_client=object(),
        db_session=object(),
    )

    import pandas as pd
    df = pd.DataFrame([
        {"system": "http://loinc.org", "code": "8867-4"},
        {"system": "http://loinc.org", "code": "invalid_code"}
    ])

    transformation = {
        "type": "enrich",
        "enrichments": [
            {
                "system_column": "system",
                "code_column": "code",
                "target_column": "display_name"
            }
        ]
    }

    res_df = await pipeline._apply_transformation(df, transformation)
    assert isinstance(res_df, pd.DataFrame)
    assert res_df["display_name"].iloc[0] == "Heart rate"
    assert res_df["display_name"].iloc[1] == ""

