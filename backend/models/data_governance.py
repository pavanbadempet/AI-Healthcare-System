"""Data governance domain models: schema contracts, violations, data catalog, and dataset lineage."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from ..database import Base


class DbSchemaContract(Base):
    __tablename__ = "schema_contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    producer = Column(String, nullable=False)
    consumer = Column(String, nullable=False)
    schema_definition = Column(JSON, nullable=False)  # Dictionary of Field -> Type
    required_fields = Column(JSON, nullable=False)    # List of required fields
    compatibility_mode = Column(String, default="BACKWARD", nullable=False)
    sla_freshness_minutes = Column(Integer, default=1440, nullable=False)
    quality_threshold = Column(Integer, default=0.95, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DbContractViolation(Base):
    __tablename__ = "contract_violations"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String, ForeignKey("schema_contracts.contract_id", ondelete="CASCADE"), index=True, nullable=False)
    errors = Column(JSON, nullable=False)  # List of validation error strings
    record_count = Column(Integer, default=1, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DbDatasetEntry(Base):
    __tablename__ = "data_catalog_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String, nullable=False)
    schema_definition = Column(JSON, nullable=False)  # Field -> Type
    tags = Column(JSON, nullable=False)                # List of tags
    sla_hours = Column(Integer, default=24, nullable=False)
    freshness_field = Column(String, default="timestamp", nullable=False)
    quality_score = Column(Integer, default=1.0, nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    location = Column(String, nullable=True)
    format = Column(String, default="json", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DbDatasetLineage(Base):
    __tablename__ = "data_catalog_lineage"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("data_catalog_datasets.dataset_id", ondelete="CASCADE"), index=True, nullable=False)
    upstream = Column(JSON, nullable=False)    # List of upstream dataset_ids
    downstream = Column(JSON, nullable=False)  # List of downstream dataset_ids
    column_lineage = Column(JSON, nullable=True)  # Dict mapping target_col -> source dict
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DbFeatureAttributionLog(Base):
    __tablename__ = "feature_attribution_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)
    features = Column(JSON, nullable=False)        # Dict of input features
    attributions = Column(JSON, nullable=False)    # Dict of SHAP values
    prediction_value = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
