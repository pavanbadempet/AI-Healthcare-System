use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Medication inventory item.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct MedicationInventory {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub medication_name: String,
    pub strength: Option<String>,
    pub form: Option<String>,
    pub batch_number: Option<String>,
    pub quantity_on_hand: f64,
    pub reorder_level: f64,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Clinical prescription header.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Prescription {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub diagnosis_context: Option<String>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
    pub dispensed_at: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// Individual prescribed medication item.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct PrescriptionItem {
    pub id: i64,
    pub prescription_id: i64,
    pub inventory_id: Option<i64>,
    pub medication_name: String,
    pub dosage: String,
    pub frequency: String,
    pub duration: String,
    pub quantity_prescribed: f64,
    pub quantity_dispensed: f64,
    pub instructions: Option<String>,
    pub status: String,
}

/// Pharmacy dispense event audit record.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DispenseRecord {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub prescription_id: i64,
    pub prescription_item_id: Option<i64>,
    pub inventory_id: Option<i64>,
    pub patient_id: i64,
    pub dispensed_by_id: Option<i64>,
    pub quantity_dispensed: f64,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}
