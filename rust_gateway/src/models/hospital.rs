use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Hospital facility tenant entity.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct HospitalFacility {
    pub id: i64,
    pub name: String,
    pub facility_type: String,
    pub country: Option<String>,
    pub region: Option<String>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Hospital clinical department.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Department {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub name: String,
    pub department_type: String,
    pub location: Option<String>,
    pub description: Option<String>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Ward inpatient bed.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Bed {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub department_id: i64,
    pub bed_number: String,
    pub ward: Option<String>,
    pub status: String,
    pub current_patient_id: Option<i64>,
    pub created_at: Option<NaiveDateTime>,
}

/// Clinical patient encounter (OPD, IPD, Emergency).
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Encounter {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub encounter_type: String,
    pub reason: Option<String>,
    pub priority: String,
    pub status: String,
    pub started_at: Option<NaiveDateTime>,
    pub ended_at: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// Inpatient hospital admission.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Admission {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: i64,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub bed_id: Option<i64>,
    pub admitted_at: Option<NaiveDateTime>,
    pub discharged_at: Option<NaiveDateTime>,
    pub reason: Option<String>,
    pub status: String,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// PACS DICOM medical imaging study metadata.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DicomStudy {
    pub id: i64,
    pub study_uid: String,
    pub patient_id: Option<i64>,
    pub modality: String,
    pub target_vault: String,
    pub file_name: String,
    pub file_size_kb: i64,
    pub is_preamble_valid: String,
    pub created_at: Option<NaiveDateTime>,
}
