use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Schema contract for data pipeline producer/consumer boundaries.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SchemaContract {
    pub id: i64,
    pub contract_id: String,
    pub name: String,
    pub version: i64,
    pub producer: String,
    pub consumer: String,
    pub schema_definition: String, // JSON
    pub required_fields: String,   // JSON
    pub compatibility_mode: String,
    pub sla_freshness_minutes: i64,
    pub quality_threshold: f64,
    pub created_at: Option<NaiveDateTime>,
    pub updated_at: Option<NaiveDateTime>,
}

/// Data contract violation incident.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ContractViolation {
    pub id: i64,
    pub contract_id: String,
    pub errors: String, // JSON
    pub record_count: i64,
    pub timestamp: Option<NaiveDateTime>,
}

/// Enterprise data catalog dataset metadata.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DataCatalogDataset {
    pub id: i64,
    pub dataset_id: String,
    pub name: String,
    pub description: Option<String>,
    pub owner: String,
    pub schema_definition: String, // JSON
    pub tags: String,              // JSON
    pub sla_hours: i64,
    pub freshness_field: String,
    pub quality_score: f64,
    pub row_count: i64,
    pub size_bytes: i64,
    pub location: Option<String>,
    pub format: String,
    pub created_at: Option<NaiveDateTime>,
    pub updated_at: Option<NaiveDateTime>,
}

/// Medallion data lineage mapping.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DataCatalogLineage {
    pub id: i64,
    pub dataset_id: String,
    pub upstream: String,   // JSON
    pub downstream: String, // JSON
    pub column_lineage: Option<String>, // JSON
    pub updated_at: Option<NaiveDateTime>,
}

/// SHAP feature attribution audit log for clinical ML explainability.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct FeatureAttributionLog {
    pub id: i64,
    pub model_name: String,
    pub model_version: String,
    pub features: String,     // JSON
    pub attributions: String, // JSON
    pub prediction_value: i64,
    pub timestamp: Option<NaiveDateTime>,
}
