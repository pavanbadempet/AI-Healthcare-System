use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Patient consent for cross-facility / ABDM FHIR interoperability.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InteroperabilityConsent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub granted_by_id: Option<i64>,
    pub revoked_by_id: Option<i64>,
    pub scope: String,
    pub purpose: Option<String>,
    pub recipient_type: String,
    pub status: String,
    pub abdm_request_id: Option<String>,
    pub abdm_consent_id: Option<String>,
    pub abdm_status: Option<String>,
    pub abdm_last_event_at: Option<NaiveDateTime>,
    pub expires_at: Option<NaiveDateTime>,
    pub revoked_at: Option<NaiveDateTime>,
    pub created_at: Option<NaiveDateTime>,
}

/// ABDM consent webhook callback notification event.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AbdmConsentEvent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub local_consent_id: Option<i64>,
    pub abdm_request_id: String,
    pub abdm_consent_id: Option<String>,
    pub event_type: String,
    pub status: String,
    pub local_consent_status: Option<String>,
    pub hi_types: Option<String>,
    pub error_code: Option<String>,
    pub notification_at: Option<NaiveDateTime>,
    pub payload_sha256: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Interoperability export destination profile.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InteroperabilityExportProfile {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub name: String,
    pub partner_system: Option<String>,
    pub resource_types: Option<String>,
    pub department_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// FHIR Bundle export audit trail with cryptographic signature.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InteroperabilityExport {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub requested_by_id: Option<i64>,
    pub consent_id: Option<i64>,
    pub profile_id: Option<i64>,
    pub export_type: String,
    pub resource_count: i64,
    pub filter_summary: Option<String>,
    pub bundle_sha256: Option<String>,
    pub manifest_signature: Option<String>,
    pub signature_algorithm: String,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Indian Ayushman Bharat Health Account (ABHA) address link.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AbhaLink {
    pub id: i64,
    pub patient_id: Option<i64>,
    pub abha_address: String,
    pub kyc_transaction_id: Option<String>,
    pub consent_purpose: String,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}
