from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pydantic import BaseModel

from backend.data_retention import DataRetentionManager
from backend.delta_lake_integration import DeltaSchemaManager, DeltaTableConfig, DeltaTableType
from backend.duckdb_client import get_duckdb_client
from backend.feature_store_client import feature_store_client

# Imports of modules to test
from backend.schema_contracts import SchemaContract, contract_registry
from backend.schema_drift_detector import schema_drift_detector

# ===========================================================================
# 1. Schema Contracts Tests
# ===========================================================================

def test_schema_contracts_validation():
    # Test registration and validation of data contracts
    contract = SchemaContract(
        contract_id="test_contract",
        name="Test Contract",
        version=1,
        producer="test_prod",
        consumer="test_cons",
        schema_definition={"id": "int", "name": "string", "active": "bool", "score": "float"},
        required_fields=["id", "name"]
    )

    # Register the contract
    contract_registry.register_contract(contract)

    # Validate correct data
    valid_data = {"id": 1, "name": "John Doe", "active": True, "score": 95.5}
    res = contract_registry.validate_data("test_contract", valid_data)
    assert res["valid"] is True
    assert res["validation_score"] == 1.0

    # Validate incorrect data (missing required field)
    invalid_data_1 = {"name": "John Doe"}
    res = contract_registry.validate_data("test_contract", invalid_data_1)
    assert res["valid"] is False
    assert any("Missing required field 'id'" in err for err in res["errors"])

    # Validate incorrect type
    invalid_data_2 = {"id": "not_an_int", "name": "John Doe"}
    res = contract_registry.validate_data("test_contract", invalid_data_2)
    assert res["valid"] is False
    assert any("expects 'int'" in err for err in res["errors"])


def test_schema_contracts_evolution_compatibility():
    old = SchemaContract(
        contract_id="evolution_test",
        name="Old Contract",
        version=1,
        producer="prod",
        consumer="cons",
        schema_definition={"id": "int", "name": "string"},
        required_fields=["id"]
    )

    # Backward compatible upgrade: adding an optional field
    new_compatible = SchemaContract(
        contract_id="evolution_test",
        name="New Contract",
        version=2,
        producer="prod",
        consumer="cons",
        schema_definition={"id": "int", "name": "string", "age": "int"},
        required_fields=["id"],
        compatibility_mode="BACKWARD"
    )

    compatible, msg = contract_registry.check_compatibility(old, new_compatible)
    assert compatible is True

    # Backward incompatible: removing a required field in new schema or changing type
    new_incompatible = SchemaContract(
        contract_id="evolution_test",
        name="Incompatible",
        version=2,
        producer="prod",
        consumer="cons",
        schema_definition={"id": "string", "name": "string"},
        required_fields=["id"],
        compatibility_mode="BACKWARD"
    )

    compatible, msg = contract_registry.check_compatibility(old, new_incompatible)
    assert compatible is False
    assert "Type of field 'id' changed" in msg

    # Evolve contract failure case
    with pytest.raises(ValueError):
        contract_registry.evolve_contract("non_existent_contract", {})


# ===========================================================================
# 2. Schema Drift Detector Tests
# ===========================================================================

class MockPydanticModel(BaseModel):
    id: int
    name: str
    email: str

class MockOrmModel:
    __tablename__ = "mock_table"
    __name__ = "MockOrmModel"

    class _Column:
        def __init__(self, name, nullable=True):
            self.name = name
            self.nullable = nullable
            self.default = None
            self.server_default = None
            self.primary_key = False

    # Define ORM columns
    id_col = _Column("id", nullable=False)
    id_col.primary_key = True
    name_col = _Column("name", nullable=False)

    __table__ = MagicMock()
    __table__.columns = {"id": id_col, "name": name_col}

def test_schema_drift_compare_pydantic_to_orm():
    # Pydantic has 'email' which is missing in ORM
    report = schema_drift_detector.compare_pydantic_to_orm(MockPydanticModel, MockOrmModel)
    assert len(report.drifts) > 0
    drift_types = [d.drift_type for d in report.drifts]
    assert "ADDED" in drift_types


def test_schema_drift_compare_orm_to_database():
    mock_engine = MagicMock()
    mock_base = MagicMock()

    # Mock DeclarativeBase metadata
    mock_table = MagicMock()
    mock_col = MagicMock()
    mock_col.name = "id"
    mock_col.type = "INTEGER"
    mock_col.nullable = False
    mock_table.columns = {"id": mock_col}
    mock_base.metadata.tables = {"mock_table": mock_table}

    # Mock sqlalchemy inspector
    with patch("backend.schema_drift_detector.inspect") as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["mock_table"]
        mock_inspector.get_columns.return_value = [{"name": "id", "type": "INTEGER", "nullable": False}]
        mock_inspect.return_value = mock_inspector

        report = schema_drift_detector.compare_orm_to_database(mock_engine, mock_base)
        assert len(report.drifts) == 0

        # Test missing table
        mock_inspector.get_table_names.return_value = []
        report = schema_drift_detector.compare_orm_to_database(mock_engine, mock_base)
        assert len(report.drifts) > 0
        assert report.drifts[0].drift_type == "REMOVED"

        # Check health status map formatting
        health_check = schema_drift_detector.as_health_check(mock_engine, mock_base)
        assert health_check["status"] in ("healthy", "degraded", "critical")


# ===========================================================================
# 3. Data Retention Manager Tests
# ===========================================================================

def test_data_retention_manager():
    mgr = DataRetentionManager()

    # Verify default policies are seeded
    report = mgr.get_retention_report()
    assert len(report) > 0

    # Legal hold
    policy = mgr.get_policy("chat_logs")
    assert policy is not None
    assert policy.legal_hold is False

    mgr.apply_legal_hold("chat_logs", "Pending litigation", "admin")
    assert policy.legal_hold is True

    mgr.release_legal_hold("chat_logs", "admin")
    assert policy.legal_hold is False

    # Evaluate retention
    mock_db = MagicMock()
    # Mocking dynamic queries for expired logs
    mock_expired_log = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_expired_log]

    expired = mgr.evaluate_retention("chat_logs", mock_db)
    assert len(expired) == 1

    # Archive records
    with patch("backend.data_retention.record_audit_event") as mock_audit:
        archived = mgr.archive_records("chat_logs", expired, mock_db, executor_id=123)
        assert archived == 1
        mock_db.delete.assert_called_with(mock_expired_log)
        mock_db.commit.assert_called()
        mock_audit.assert_called_once()


# ===========================================================================
# 4. DuckDB Client Tests
# ===========================================================================

def test_duckdb_client():
    # Instantiate in-memory DuckDB connection client
    client = get_duckdb_client(":memory:")
    assert client.conn is not None

    # Execute query returning List[Dict]
    res = client.execute_query("SELECT 1 as val, 'health' as type")
    assert len(res) == 1
    assert res[0]["val"] == 1
    assert res[0]["type"] == "health"

    # Execute to Pandas DataFrame
    df = client.execute_to_df("SELECT 100 as count")
    assert isinstance(df, pd.DataFrame)
    assert df["count"].iloc[0] == 100

    # Query delta table path checks
    empty_res = client.query_delta_table("non_existent_delta_path")
    assert empty_res == []

    client.close()


# ===========================================================================
# 5. Delta Lake Integration Tests
# ===========================================================================

def test_delta_lake_integration():
    mock_spark = MagicMock()
    mock_spark.sql = MagicMock()

    mock_df = MagicMock()
    mock_df.count.return_value = 50

    config = DeltaTableConfig(
        table_name="patients",
        table_type=DeltaTableType.DIMENSION,
        cluster_columns=["patient_id"]
    )

    manager = DeltaSchemaManager(mock_spark)

    # Mock Spark writer Options pattern
    mock_writer = MagicMock()
    mock_df.write.format.return_value = mock_writer
    mock_writer.clusterBy.return_value = mock_writer
    mock_writer.mode.return_value = mock_writer
    mock_writer.options.return_value = mock_writer

    with patch("backend.delta_lake_integration.DeltaTable.forPath", create=True):
        res = manager.create_delta_table(mock_df, config, path="/tmp/test_delta")
        assert res["status"] == "success"
        assert res["record_count"] == 50

    # Evolve schema changes check
    schema_changes = [
        {"type": "ADD_COLUMN", "column_name": "middle_name", "data_type": "STRING"},
        {"type": "DROP_COLUMN", "column_name": "temp_col"},
        {"type": "RENAME_COLUMN", "old_column_name": "email", "new_column_name": "email_address"},
        {"type": "MODIFY_TYPE", "column_name": "age", "new_data_type": "DOUBLE"},
        {"type": "UPDATE_COLUMN_DESCRIPTION", "column_name": "phone", "description": "Mobile number"}
    ]

    evolve_res = manager.evolve_schema("patients", schema_changes)
    assert evolve_res["changes_applied"] == 5
    assert mock_spark.sql.call_count > 0


# ===========================================================================
# 6. Feature Store Client Tests
# ===========================================================================

def test_feature_store_client():
    assert feature_store_client is not None
    # By default FEAST_REPO_PATH is not set in test environment, so it falls back gracefully
    assert feature_store_client.is_available is False

    # Retrieve features should degrade gracefully and return None
    res = feature_store_client.get_online_features(
        entity_ids=[{"patient_id": 42}],
        feature_refs=["patient_vitals:heart_rate"]
    )
    assert res is None

    # Feature group lookup helpers
    group = feature_store_client.get_feature_group("patient_vitals")
    assert group is not None
    assert "patient_vitals:heart_rate" in group.features

    # List feature groups
    groups = feature_store_client.list_feature_groups()
    assert "patient_vitals" in groups


# ===========================================================================
# 7. Data Catalog Tests
# ===========================================================================

def test_data_catalog_persistence():
    from backend.data_catalog import DatasetEntry, data_catalog

    entry = DatasetEntry(
        dataset_id="test_catalog_dataset",
        name="Test Catalog Dataset",
        description="Testing SQL backing and metadata persistence",
        owner="ml_team",
        schema={"id": "int", "value": "float"},
        tags=["test", "ml"]
    )

    # Register dataset
    data_catalog.register_dataset(entry)

    # Verify retrieval
    retrieved = data_catalog.get_dataset("test_catalog_dataset")
    assert retrieved is not None
    assert retrieved.name == "Test Catalog Dataset"
    assert "test" in retrieved.tags

    # Update quality score
    data_catalog.update_quality_score("test_catalog_dataset", 0.98)
    retrieved = data_catalog.get_dataset("test_catalog_dataset")
    assert retrieved.quality_score == 0.98

    # Add dependency lineage
    data_catalog.add_lineage("patient_accounts", "test_catalog_dataset")
    lineage = data_catalog.get_lineage("test_catalog_dataset")
    assert "patient_accounts" in lineage["upstream"]


def test_expectation_runner_chunked_validation():
    from backend.data_expectations import Expectation, ExpectationRunner
    runner = ExpectationRunner()
    runner.create_suite("test_chunked_suite", "test_dataset")
    runner.add_expectation("test_chunked_suite", Expectation("expect_column_values_between", "val", {"min_value": 0, "max_value": 10}))
    runner.add_expectation("test_chunked_suite", Expectation("expect_column_mean_between", "val", {"min_value": 3, "max_value": 6}))
    runner.add_expectation("test_chunked_suite", Expectation("expect_table_row_count_between", "val", {"min_value": 5, "max_value": 15}))
    runner.add_expectation("test_chunked_suite", Expectation("expect_column_unique_value_count_between", "val", {"min_value": 2, "max_value": 10}))

    # 10 rows: if chunk_size = 3, it will trigger chunked validation pathway
    data = [{"val": 2}, {"val": 3}, {"val": 4}, {"val": 5}, {"val": 6}, {"val": 2}, {"val": 3}, {"val": 4}, {"val": 5}, {"val": 6}]
    report = runner.validate("test_chunked_suite", data, chunk_size=3)
    assert report.success is True
    assert report.success_rate == 1.0

    # Test out of bounds failure in chunked pathway
    data_fail = [{"val": 2}, {"val": 30}]
    report_fail = runner.validate("test_chunked_suite", data_fail, chunk_size=1)
    assert report_fail.success is False


def test_column_level_lineage():
    from backend.data_catalog import data_catalog
    data_catalog.add_column_lineage(
        dataset_id="gold_health_insights",
        target_col="test_target",
        source_dataset="patient_accounts",
        source_col="test_source",
        transform="anonymized"
    )
    lineage = data_catalog.get_lineage("gold_health_insights")
    assert "column_lineage" in lineage
    assert lineage["column_lineage"]["test_target"]["source_dataset"] == "patient_accounts"
    assert lineage["column_lineage"]["test_target"]["source_column"] == "test_source"
    assert lineage["column_lineage"]["test_target"]["transform"] == "anonymized"


def test_schema_drift_detector_normalization():
    from backend.schema_drift_detector import schema_drift_detector
    assert schema_drift_detector._normalize_type("VARCHAR(255)") == "VARCHAR"
    assert schema_drift_detector._normalize_type("JSONB") == "VARCHAR"
    assert schema_drift_detector._normalize_type("BIGINT") == "INTEGER"
    assert schema_drift_detector._normalize_type("FLOAT8") == "DECIMAL"
    assert schema_drift_detector._normalize_type("DATE") == "TIMESTAMP"


