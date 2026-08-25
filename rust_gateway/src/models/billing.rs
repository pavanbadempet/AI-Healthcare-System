use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Billable service catalog model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BillableService {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub service_code: String,
    pub name: String,
    pub service_type: String,
    pub department_id: Option<i64>,
    pub unit_price: f64,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Invoice model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Invoice {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub encounter_id: Option<i64>,
    pub admission_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub status: String,
    pub subtotal: f64,
    pub discount_amount: f64,
    pub tax_amount: f64,
    pub total_amount: f64,
    pub paid_amount: f64,
    pub balance_amount: f64,
    pub currency: String,
    pub created_at: Option<NaiveDateTime>,
    pub issued_at: Option<NaiveDateTime>,
}

/// Invoice line item model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InvoiceLineItem {
    pub id: i64,
    pub invoice_id: i64,
    pub service_id: Option<i64>,
    pub description: String,
    pub quantity: f64,
    pub unit_price: f64,
    pub line_total: f64,
}

/// Billing payment model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BillingPayment {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub invoice_id: i64,
    pub patient_id: i64,
    pub collected_by_id: Option<i64>,
    pub amount: f64,
    pub payment_method: String,
    pub reference_id: Option<String>,
    pub status: String,
    pub collected_at: Option<NaiveDateTime>,
}

/// Insurance claim model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct InsuranceClaim {
    pub id: i64,
    pub claim_number: String,
    pub patient_name: String,
    pub payer_name: String,
    pub policy_id: String,
    pub claim_amount: f64,
    pub copay_amount: f64,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}
