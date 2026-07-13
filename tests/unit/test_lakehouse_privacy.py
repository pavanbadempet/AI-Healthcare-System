import importlib
import sys
import types


def _install_lakehouse_stubs(monkeypatch, delta_table_class=None):
    for module_name in [
        "backend.advanced_data_modeling",
        "backend.delta_lake_integration",
        "backend.production_healthcare_modeling",
        "pyspark",
        "pyspark.sql",
        "pyspark.sql.functions",
        "pyspark.sql.types",
        "delta",
        "delta.tables",
    ]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    pyspark = types.ModuleType("pyspark")
    pyspark_sql = types.ModuleType("pyspark.sql")
    pyspark_functions = types.ModuleType("pyspark.sql.functions")
    pyspark_types = types.ModuleType("pyspark.sql.types")
    delta_module = types.ModuleType("delta")
    delta_tables = types.ModuleType("delta.tables")

    class SparkSession:
        pass

    class SparkDF:
        pass

    class Window:
        pass

    class _SparkType:
        def __init__(self, *args, **kwargs):
            self.fields = []

        def add(self, *args, **kwargs):
            return self

    def _function_stub(*args, **kwargs):
        return None

    pyspark_sql.SparkSession = SparkSession
    pyspark_sql.DataFrame = SparkDF
    pyspark_sql.Window = Window
    for name in ["col", "lit", "current_timestamp", "row_number"]:
        setattr(pyspark_functions, name, _function_stub)
    for name in ["StructType", "StructField", "StringType", "TimestampType"]:
        setattr(pyspark_types, name, _SparkType)
    delta_tables.DeltaTable = delta_table_class or type("DeltaTable", (), {})

    monkeypatch.setitem(sys.modules, "pyspark", pyspark)
    monkeypatch.setitem(sys.modules, "pyspark.sql", pyspark_sql)
    monkeypatch.setitem(sys.modules, "pyspark.sql.functions", pyspark_functions)
    monkeypatch.setitem(sys.modules, "pyspark.sql.types", pyspark_types)
    monkeypatch.setitem(sys.modules, "delta", delta_module)
    monkeypatch.setitem(sys.modules, "delta.tables", delta_tables)


class FailingSpark:
    def __init__(self, message: str):
        self.message = message

    def table(self, table_name):
        raise RuntimeError(self.message)


class FailingDeltaTable:
    message = ""

    @classmethod
    def forPath(cls, spark, path):
        raise RuntimeError(cls.message)

    @classmethod
    def forName(cls, spark, name):
        raise RuntimeError(cls.message)


class FakeDeltaWriter:
    def __init__(self):
        self.saved_paths = []
        self.saved_tables = []

    def format(self, source_format):
        self.source_format = source_format
        return self

    def clusterBy(self, *columns):
        self.cluster_columns = columns
        return self

    def mode(self, write_mode):
        self.write_mode = write_mode
        return self

    def options(self, **options):
        self.write_options = options
        return self

    def save(self, path):
        self.saved_paths.append(path)

    def saveAsTable(self, table_name):
        self.saved_tables.append(table_name)


class FakeDeltaDataFrame:
    def __init__(self):
        self.write = FakeDeltaWriter()

    def count(self):
        return 0


class CapturingSpark:
    def __init__(self):
        self.sql_statements = []

    def sql(self, statement):
        self.sql_statements.append(statement)


def test_advanced_schema_evolution_hides_failure_details(monkeypatch, caplog):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.advanced_data_modeling")
    sensitive_error = "spark password=modeling-secret patient_name=Sensitive User"
    manager = module.SchemaEvolutionManager(FailingSpark(sensitive_error))
    caplog.set_level("ERROR", logger="backend.advanced_data_modeling")

    result = manager.apply_schema_evolution(
        "patients",
        types.SimpleNamespace(schema=types.SimpleNamespace(fields=[])),
        module.TableFormat.DELTA,
    )

    assert result == {
        "status": "failed",
        "table": "patients",
        "error": module.DATA_MODELING_FAILURE_MESSAGE,
    }
    assert sensitive_error not in str(result)
    assert "modeling-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_delta_create_table_rejects_unsafe_table_identifier(monkeypatch):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    manager = module.DeltaSchemaManager(CapturingSpark())
    config = module.DeltaTableConfig(
        table_name="patients; DROP TABLE users",
        table_type=module.DeltaTableType.DIMENSION,
    )

    try:
        manager.create_delta_table(FakeDeltaDataFrame(), config)
    except ValueError as exc:
        assert "Invalid Delta table_name" in str(exc)
    else:
        raise AssertionError("unsafe Delta table identifiers must be rejected")


def test_delta_create_table_escapes_external_location(monkeypatch):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    spark = CapturingSpark()
    manager = module.DeltaSchemaManager(spark)
    config = module.DeltaTableConfig(
        table_name="patients",
        table_type=module.DeltaTableType.DIMENSION,
        cluster_columns=[],
    )

    result = manager.create_delta_table(FakeDeltaDataFrame(), config, path="/mnt/delta/patient's")

    assert result["status"] == "success"
    assert spark.sql_statements == [
        "CREATE TABLE IF NOT EXISTS uc_healthcare_prod.healthcare_db.patients "
        "USING DELTA LOCATION '/mnt/delta/patient''s'"
    ]


def test_delta_schema_evolution_hides_failure_details(monkeypatch, caplog):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    sensitive_error = "delta password=delta-secret patient_name=Sensitive User"
    manager = module.DeltaSchemaManager(spark=object())

    def fail_add_column(table_name, change):
        raise RuntimeError(sensitive_error)

    manager._add_column = fail_add_column
    caplog.set_level("ERROR", logger="backend.delta_lake_integration")

    result = manager.evolve_schema("patients", [{"type": "ADD_COLUMN", "column_name": "x"}])

    assert result["error_details"] == [module.DELTA_OPERATION_FAILURE_MESSAGE]
    assert sensitive_error not in str(result)
    assert "delta-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_delta_schema_evolution_rejects_unsafe_column_identifier(monkeypatch):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    spark = CapturingSpark()
    manager = module.DeltaSchemaManager(spark)

    result = manager.evolve_schema(
        "healthcare_db.lab_results",
        [{
            "type": "ADD_COLUMN",
            "column_name": "result_bad; DROP TABLE patients",
            "data_type": "FLOAT",
        }],
    )

    assert result["changes_applied"] == 0
    assert result["errors"] == 1
    assert result["error_details"] == [module.DELTA_OPERATION_FAILURE_MESSAGE]
    assert spark.sql_statements == []


def test_delta_schema_evolution_escapes_column_description(monkeypatch):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    spark = CapturingSpark()
    manager = module.DeltaSchemaManager(spark)

    result = manager.evolve_schema(
        "healthcare_db.lab_results",
        [{
            "type": "UPDATE_COLUMN_DESCRIPTION",
            "column_name": "result_glucose",
            "description": "O'Brien reference range",
        }],
    )

    assert result["changes_applied"] == 1
    assert result["errors"] == 0
    assert spark.sql_statements == [
        "ALTER TABLE healthcare_db.lab_results ALTER COLUMN result_glucose COMMENT 'O''Brien reference range'"
    ]


def test_healthcare_delta_compliance_report_hides_failure_details(monkeypatch, caplog):
    _install_lakehouse_stubs(monkeypatch)
    module = importlib.import_module("backend.delta_lake_integration")
    sensitive_error = "history password=report-secret patient_name=Sensitive User"
    manager = object.__new__(module.HealthcareDeltaManager)
    manager.schema_manager = types.SimpleNamespace(
        get_table_history=lambda table_name: (_ for _ in ()).throw(RuntimeError(sensitive_error))
    )
    caplog.set_level("ERROR", logger="backend.delta_lake_integration")

    result = manager.get_compliance_report("patients")

    assert result == {
        "table_name": "patients",
        "compliance_status": "error",
        "error": module.DELTA_OPERATION_FAILURE_MESSAGE,
    }
    assert sensitive_error not in str(result)
    assert "report-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_production_modeling_hides_failure_details(monkeypatch, caplog):
    sensitive_error = "delta password=prod-secret patient_name=Sensitive User"
    FailingDeltaTable.message = sensitive_error
    _install_lakehouse_stubs(monkeypatch, delta_table_class=FailingDeltaTable)
    module = importlib.import_module("backend.production_healthcare_modeling")
    modeler = module.ProductionHealthcareModeler(spark=object(), warehouse_path="/warehouse")
    caplog.set_level("ERROR", logger="backend.production_healthcare_modeling")

    vacuum_result = modeler.run_vacuum_safely("patients")
    metrics_result = modeler.get_performance_metrics("patients")

    assert vacuum_result["error"] == module.PRODUCTION_MODELING_FAILURE_MESSAGE
    assert metrics_result == {"error": module.PRODUCTION_MODELING_FAILURE_MESSAGE}
    assert sensitive_error not in str(vacuum_result)
    assert sensitive_error not in str(metrics_result)
    assert "prod-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
