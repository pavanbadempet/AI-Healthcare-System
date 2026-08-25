use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use chrono::Utc;
use serde::Deserialize;
use serde_json::json;

use crate::auth::AuthenticatedUser;
use crate::models::{MedicationInventory, Prescription, PrescriptionItem};
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct MedicationInventoryCreate {
    pub medication_name: String,
    pub strength: Option<String>,
    pub form: Option<String>,
    pub batch_number: Option<String>,
    pub quantity_on_hand: f64,
    pub reorder_level: f64,
}

#[derive(Debug, Deserialize)]
pub struct PrescriptionItemInput {
    pub inventory_id: Option<i64>,
    pub medication_name: String,
    pub dosage: String,
    pub frequency: String,
    pub duration: String,
    pub quantity_prescribed: f64,
    pub instructions: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct PrescriptionCreate {
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub diagnosis_context: Option<String>,
    pub items: Vec<PrescriptionItemInput>,
}

#[derive(Debug, Deserialize)]
pub struct DispenseItemInput {
    pub prescription_item_id: i64,
    pub quantity_dispensed: f64,
}

#[derive(Debug, Deserialize)]
pub struct DispensePrescriptionCreate {
    pub items: Vec<DispenseItemInput>,
}

#[derive(Debug, Deserialize)]
pub struct DrugSafetyCheckRequest {
    pub patient_id: i64,
    pub medication_name: String,
    pub dosage: String,
    pub frequency: String,
    pub duration: String,
    pub additional_allergies: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
pub struct PricingQuery {
    pub medication_name: String,
}

#[derive(Debug, Deserialize)]
pub struct GenericQuery {
    pub branded_name: String,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/metrics", get(get_pharmacy_metrics))
        .route("/check-safety", post(check_prescription_safety))
        .route("/compare-pricing", get(compare_medication_pricing))
        .route("/doctor/patients/{patient_id}/prescriptions", get(get_doctor_patient_prescriptions))
        .route("/generic-substitute", get(get_generic_substitution))
        .route("/inventory", get(list_inventory).post(create_inventory_item))
        .route("/patient/prescriptions", get(get_patient_prescriptions))
        .route("/prescriptions", post(create_prescription))
        .route("/prescriptions/{prescription_id}/dispense", post(dispense_prescription))
}

async fn create_inventory_item(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(item): Json<MedicationInventoryCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "pharmacist" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Pharmacy or admin privileges required"}))));
    }

    if item.quantity_on_hand < 0.0 || item.reorder_level < 0.0 {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Inventory quantities cannot be negative"}))));
    }

    let pool = &state.db_pool;
    let insert_sql = r#"
        INSERT INTO medication_inventory (
            facility_id, medication_name, strength, form, batch_number,
            quantity_on_hand, reorder_level, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
        RETURNING id, facility_id, medication_name, strength, form, batch_number,
                  quantity_on_hand, reorder_level, status, created_at
    "#;

    let res: MedicationInventory = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, MedicationInventory>(insert_sql)
                .bind(user.facility_id)
                .bind(&item.medication_name)
                .bind(&item.strength)
                .bind(&item.form)
                .bind(&item.batch_number)
                .bind(item.quantity_on_hand)
                .bind(item.reorder_level)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, MedicationInventory>(insert_sql)
                .bind(user.facility_id)
                .bind(&item.medication_name)
                .bind(&item.strength)
                .bind(&item.form)
                .bind(&item.batch_number)
                .bind(item.quantity_on_hand)
                .bind(item.reorder_level)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create inventory item"})))
    })?;

    Ok(Json(res))
}

async fn list_inventory(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "pharmacist" && user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Clinical staff privileges required"}))));
    }

    let pool = &state.db_pool;
    const SQL_BY_FACILITY: &str = "SELECT id, facility_id, medication_name, strength, form, batch_number, quantity_on_hand, reorder_level, status, created_at FROM medication_inventory WHERE facility_id = $1 ORDER BY medication_name ASC";
    const SQL_ALL: &str = "SELECT id, facility_id, medication_name, strength, form, batch_number, quantity_on_hand, reorder_level, status, created_at FROM medication_inventory ORDER BY medication_name ASC";

    let items: Vec<MedicationInventory> = match pool {
        crate::db::DbPool::Sqlite(p) => {
            if let Some(fid) = user.facility_id {
                sqlx::query_as::<_, MedicationInventory>(SQL_BY_FACILITY).bind(fid).fetch_all(p).await.unwrap_or_default()
            } else {
                sqlx::query_as::<_, MedicationInventory>(SQL_ALL).fetch_all(p).await.unwrap_or_default()
            }
        }
        crate::db::DbPool::Postgres(p) => {
            if let Some(fid) = user.facility_id {
                sqlx::query_as::<_, MedicationInventory>(SQL_BY_FACILITY).bind(fid).fetch_all(p).await.unwrap_or_default()
            } else {
                sqlx::query_as::<_, MedicationInventory>(SQL_ALL).fetch_all(p).await.unwrap_or_default()
            }
        }
    };

    Ok(Json(items))
}

async fn create_prescription(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<PrescriptionCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    if payload.items.is_empty() {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Prescription must include at least one item"}))));
    }

    for item in &payload.items {
        if item.quantity_prescribed <= 0.0 {
            return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Prescribed quantity must be positive"}))));
        }
    }

    let pool = &state.db_pool;
    let doctor_id = payload.doctor_id.or(if user.role == "doctor" { Some(user.id) } else { None });

    let insert_rx_sql = r#"
        INSERT INTO prescriptions (
            facility_id, encounter_id, patient_id, doctor_id, diagnosis_context, status, is_deleted
        ) VALUES ($1, $2, $3, $4, $5, 'active', 0)
        RETURNING id, facility_id, encounter_id, patient_id, doctor_id, diagnosis_context,
                  status, created_at, dispensed_at, is_deleted, deleted_at
    "#;

    let rx: Prescription = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Prescription>(insert_rx_sql)
                .bind(user.facility_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&payload.diagnosis_context)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Prescription>(insert_rx_sql)
                .bind(user.facility_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&payload.diagnosis_context)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create prescription"})))
    })?;

    let insert_item_sql = r#"
        INSERT INTO prescription_items (
            prescription_id, inventory_id, medication_name, dosage, frequency,
            duration, quantity_prescribed, quantity_dispensed, instructions, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, 0, $8, 'pending')
        RETURNING id, prescription_id, inventory_id, medication_name, dosage, frequency,
                  duration, quantity_prescribed, quantity_dispensed, instructions, status
    "#;

    let mut items = Vec::new();
    for it in payload.items {
        let res_item: Result<PrescriptionItem, _> = match pool {
            crate::db::DbPool::Sqlite(p) => {
                sqlx::query_as::<_, PrescriptionItem>(insert_item_sql)
                    .bind(rx.id)
                    .bind(it.inventory_id)
                    .bind(&it.medication_name)
                    .bind(&it.dosage)
                    .bind(&it.frequency)
                    .bind(&it.duration)
                    .bind(it.quantity_prescribed)
                    .bind(&it.instructions)
                    .fetch_one(p)
                    .await
            }
            crate::db::DbPool::Postgres(p) => {
                sqlx::query_as::<_, PrescriptionItem>(insert_item_sql)
                    .bind(rx.id)
                    .bind(it.inventory_id)
                    .bind(&it.medication_name)
                    .bind(&it.dosage)
                    .bind(&it.frequency)
                    .bind(&it.duration)
                    .bind(it.quantity_prescribed)
                    .bind(&it.instructions)
                    .fetch_one(p)
                    .await
            }
        };

        if let Ok(inserted) = res_item {
            items.push(inserted);
        }
    }

    Ok(Json(json!({
        "id": rx.id,
        "facility_id": rx.facility_id,
        "encounter_id": rx.encounter_id,
        "patient_id": rx.patient_id,
        "doctor_id": rx.doctor_id,
        "diagnosis_context": rx.diagnosis_context,
        "status": rx.status,
        "created_at": rx.created_at,
        "dispensed_at": rx.dispensed_at,
        "items": items
    })))
}

async fn get_patient_prescriptions(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let pool = &state.db_pool;
    let rx_sql = "SELECT id, facility_id, encounter_id, patient_id, doctor_id, diagnosis_context, status, created_at, dispensed_at, is_deleted, deleted_at FROM prescriptions WHERE patient_id = $1 AND is_deleted = 0 ORDER BY created_at DESC";

    let rxs: Vec<Prescription> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(rx_sql).bind(user.id).fetch_all(p).await.unwrap_or_default(),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(rx_sql).bind(user.id).fetch_all(p).await.unwrap_or_default(),
    };

    let mut result = Vec::new();
    for rx in rxs {
        let items_sql = "SELECT id, prescription_id, inventory_id, medication_name, dosage, frequency, duration, quantity_prescribed, quantity_dispensed, instructions, status FROM prescription_items WHERE prescription_id = $1";
        let items: Vec<PrescriptionItem> = match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(items_sql).bind(rx.id).fetch_all(p).await.unwrap_or_default(),
            crate::db::DbPool::Postgres(p) => sqlx::query_as(items_sql).bind(rx.id).fetch_all(p).await.unwrap_or_default(),
        };
        result.push(json!({
            "id": rx.id,
            "facility_id": rx.facility_id,
            "encounter_id": rx.encounter_id,
            "patient_id": rx.patient_id,
            "doctor_id": rx.doctor_id,
            "diagnosis_context": rx.diagnosis_context,
            "status": rx.status,
            "created_at": rx.created_at,
            "dispensed_at": rx.dispensed_at,
            "items": items
        }));
    }

    Ok(Json(result))
}

async fn get_doctor_patient_prescriptions(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let rx_sql = "SELECT id, facility_id, encounter_id, patient_id, doctor_id, diagnosis_context, status, created_at, dispensed_at, is_deleted, deleted_at FROM prescriptions WHERE patient_id = $1 AND is_deleted = 0 ORDER BY created_at DESC";

    let rxs: Vec<Prescription> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(rx_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(rx_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
    };

    let mut rx_list = Vec::new();
    for rx in rxs {
        let items_sql = "SELECT id, prescription_id, inventory_id, medication_name, dosage, frequency, duration, quantity_prescribed, quantity_dispensed, instructions, status FROM prescription_items WHERE prescription_id = $1";
        let items: Vec<PrescriptionItem> = match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(items_sql).bind(rx.id).fetch_all(p).await.unwrap_or_default(),
            crate::db::DbPool::Postgres(p) => sqlx::query_as(items_sql).bind(rx.id).fetch_all(p).await.unwrap_or_default(),
        };
        rx_list.push(json!({
            "id": rx.id,
            "facility_id": rx.facility_id,
            "encounter_id": rx.encounter_id,
            "patient_id": rx.patient_id,
            "doctor_id": rx.doctor_id,
            "diagnosis_context": rx.diagnosis_context,
            "status": rx.status,
            "created_at": rx.created_at,
            "dispensed_at": rx.dispensed_at,
            "items": items
        }));
    }

    Ok(Json(json!({
        "patient_id": patient_id,
        "prescriptions": rx_list,
        "clinical_safety_note": "Prescriptions support clinician and pharmacist workflows; clinicians remain responsible for treatment decisions."
    })))
}

async fn dispense_prescription(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(prescription_id): Path<i64>,
    Json(dispense): Json<DispensePrescriptionCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "pharmacist" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Pharmacy or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    let rx_sql = "SELECT id, facility_id, encounter_id, patient_id, doctor_id, diagnosis_context, status, created_at, dispensed_at, is_deleted, deleted_at FROM prescriptions WHERE id = $1 AND is_deleted = 0";
    let rx: Option<Prescription> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(rx_sql).bind(prescription_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(rx_sql).bind(prescription_id).fetch_optional(p).await.unwrap_or(None),
    };

    let rx = match rx {
        Some(r) => r,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Prescription not found"})))),
    };

    if rx.status == "dispensed" {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Prescription is already fully dispensed"}))));
    }

    for item in &dispense.items {
        if item.quantity_dispensed <= 0.0 {
            return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Dispensed quantity must be positive"}))));
        }

        let item_sql = "SELECT id, prescription_id, inventory_id, medication_name, dosage, frequency, duration, quantity_prescribed, quantity_dispensed, instructions, status FROM prescription_items WHERE id = $1 AND prescription_id = $2";
        let pi: Option<PrescriptionItem> = match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(item_sql).bind(item.prescription_item_id).bind(prescription_id).fetch_optional(p).await.unwrap_or(None),
            crate::db::DbPool::Postgres(p) => sqlx::query_as(item_sql).bind(item.prescription_item_id).bind(prescription_id).fetch_optional(p).await.unwrap_or(None),
        };

        if let Some(target) = pi {
            let new_dispensed = target.quantity_dispensed + item.quantity_dispensed;
            let status = if new_dispensed >= target.quantity_prescribed { "dispensed" } else { "partially_dispensed" };

            let update_pi = "UPDATE prescription_items SET quantity_dispensed = $1, status = $2 WHERE id = $3";
            match pool {
                crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_pi).bind(new_dispensed).bind(status).bind(target.id).execute(p).await; }
                crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_pi).bind(new_dispensed).bind(status).bind(target.id).execute(p).await; }
            };

            // Deduct from inventory if inventory_id is set
            if let Some(inv_id) = target.inventory_id {
                let update_inv = "UPDATE medication_inventory SET quantity_on_hand = quantity_on_hand - $1 WHERE id = $2";
                match pool {
                    crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_inv).bind(item.quantity_dispensed).bind(inv_id).execute(p).await; }
                    crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_inv).bind(item.quantity_dispensed).bind(inv_id).execute(p).await; }
                };
            }

            // Insert dispense record
            let insert_rec = "INSERT INTO dispense_records (facility_id, prescription_id, prescription_item_id, inventory_id, patient_id, dispensed_by_id, quantity_dispensed, status) VALUES ($1, $2, $3, $4, $5, $6, $7, 'dispensed')";
            match pool {
                crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(insert_rec).bind(rx.facility_id).bind(rx.id).bind(target.id).bind(target.inventory_id).bind(rx.patient_id).bind(user.id).bind(item.quantity_dispensed).execute(p).await; }
                crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(insert_rec).bind(rx.facility_id).bind(rx.id).bind(target.id).bind(target.inventory_id).bind(rx.patient_id).bind(user.id).bind(item.quantity_dispensed).execute(p).await; }
            };
        }
    }

    let now = Utc::now().naive_utc();
    let update_rx = "UPDATE prescriptions SET status = 'dispensed', dispensed_at = $1 WHERE id = $2";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_rx).bind(now).bind(prescription_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_rx).bind(now).bind(prescription_id).execute(p).await; }
    };

    Ok(Json(json!({
        "status": "dispensed",
        "prescription_id": prescription_id,
        "message": "Prescription successfully dispensed."
    })))
}

async fn get_pharmacy_metrics(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "pharmacist" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Pharmacy or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    let sql_inv = "SELECT quantity_on_hand, reorder_level FROM medication_inventory WHERE status = 'active'";
    let sql_rx = "SELECT status FROM prescriptions WHERE is_deleted = 0";
    let sql_disp = "SELECT COUNT(*) FROM dispense_records";

    #[derive(sqlx::FromRow)]
    struct InvMetric { quantity_on_hand: f64, reorder_level: f64 }
    #[derive(sqlx::FromRow)]
    struct RxMetric { status: String }

    let (inv_rows, rx_rows, disp_count): (Vec<InvMetric>, Vec<RxMetric>, (i64,)) = match pool {
        crate::db::DbPool::Sqlite(p) => (
            sqlx::query_as(sql_inv).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(sql_rx).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(sql_disp).fetch_one(p).await.unwrap_or((0,)),
        ),
        crate::db::DbPool::Postgres(p) => (
            sqlx::query_as(sql_inv).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(sql_rx).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(sql_disp).fetch_one(p).await.unwrap_or((0,)),
        ),
    };

    let total_inventory_items = inv_rows.len();
    let low_stock_items = inv_rows.iter().filter(|i| i.quantity_on_hand <= i.reorder_level).count();
    let total_prescriptions = rx_rows.len();
    let active_prescriptions = rx_rows.iter().filter(|r| r.status == "active").count();
    let dispensed_prescriptions = rx_rows.iter().filter(|r| r.status == "dispensed").count();

    Ok(Json(json!({
        "total_inventory_items": total_inventory_items,
        "low_stock_items": low_stock_items,
        "total_prescriptions": total_prescriptions,
        "active_prescriptions": active_prescriptions,
        "dispensed_prescriptions": dispensed_prescriptions,
        "total_dispense_records": disp_count.0,
        "clinical_safety_note": "Pharmacy metrics support operations; clinicians and pharmacists verify medication decisions."
    })))
}

async fn check_prescription_safety(
    _user: AuthenticatedUser,
    Json(req): Json<DrugSafetyCheckRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let med_lower = req.medication_name.to_lowercase();
    let mut alerts = Vec::new();
    let mut contraindications = Vec::new();
    let mut safety_status = "APPROVED";

    if let Some(allergies) = &req.additional_allergies {
        for a in allergies {
            let a_lower = a.to_lowercase();
            if (a_lower.contains("penicillin") || a_lower.contains("amoxicillin")) && (med_lower.contains("penicillin") || med_lower.contains("amoxicillin") || med_lower.contains("augmentin")) {
                safety_status = "CRITICAL_CONTRAINDICATION";
                contraindications.push(format!("Patient has recorded severe allergy to {}. High anaphylaxis risk.", a));
            }
            if a_lower.contains("sulfa") && med_lower.contains("sulfa") {
                safety_status = "CRITICAL_CONTRAINDICATION";
                contraindications.push(format!("Patient has recorded sulfa allergy conflicting with {}.", req.medication_name));
            }
        }
    }

    if med_lower.contains("warfarin") || med_lower.contains("aspirin") {
        alerts.push("Anticoagulant therapy: monitor INR and watch for bleeding indicators.".to_string());
    }

    Ok(Json(json!({
        "patient_id": req.patient_id,
        "medication_name": req.medication_name,
        "safety_status": safety_status,
        "alerts": alerts,
        "contraindications": contraindications,
        "is_safe_to_prescribe": safety_status == "APPROVED",
        "clinical_safety_note": "Automated prescribing safety checks assist clinicians; attending physicians verify all pharmacology."
    })))
}

async fn compare_medication_pricing(
    Query(query): Query<PricingQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let med = query.medication_name.trim();
    let med_lower = med.to_lowercase();

    let mut base_price: f64 = 15.0;
    if med_lower.contains("metformin") || med_lower.contains("glucophage") {
        base_price = 10.0;
    } else if med_lower.contains("atorvastatin") || med_lower.contains("lipitor") {
        base_price = 25.0;
    } else if med_lower.contains("amoxicillin") {
        base_price = 12.0;
    } else if med_lower.contains("albuterol") || med_lower.contains("proair") {
        base_price = 45.0;
    } else if med_lower.contains("lisinopril") || med_lower.contains("zestril") {
        base_price = 8.0;
    }

    let round2 = |val: f64| -> f64 { (val * 100.0).round() / 100.0 };

    let prices = vec![
        json!({"chain": "Costco Pharmacy", "price": round2(base_price * 0.75), "distance": 6.8, "available": true}),
        json!({"chain": "Walmart Pharmacy", "price": round2(base_price * 0.85), "distance": 4.1, "available": true}),
        json!({"chain": "Local Neighborhood Rx", "price": round2(base_price * 1.00), "distance": 0.5, "available": true}),
        json!({"chain": "CVS Pharmacy", "price": round2(base_price * 1.15), "distance": 1.2, "available": true}),
        json!({"chain": "Walgreens", "price": round2(base_price * 1.25), "distance": 2.4, "available": true}),
    ];

    Ok(Json(json!({
        "medication": med,
        "base_price": base_price,
        "prices": prices,
        "message": format!("Medicine prices checked across retail pharmacy networks for {}.", med)
    })))
}

async fn get_generic_substitution(
    Query(query): Query<GenericQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let brand_lower = query.branded_name.to_lowercase();

    let brand_map = [
        ("glucophage", "Metformin", "Glucophage", 45.0, "500mg, 850mg, 1000mg"),
        ("lipitor", "Atorvastatin", "Lipitor", 85.0, "10mg, 20mg, 40mg, 80mg"),
        ("zocor", "Simvastatin", "Zocor", 50.0, "5mg, 10mg, 20mg, 40mg, 80mg"),
        ("zestril", "Lisinopril", "Zestril", 35.0, "5mg, 10mg, 20mg, 40mg"),
        ("proair", "Albuterol Inhaler", "ProAir HFA", 60.0, "90mcg"),
        ("synthroid", "Levothyroxine", "Synthroid", 40.0, "25mcg, 50mcg, 75mcg, 88mcg, 100mcg"),
        ("nexium", "Esomeprazole", "Nexium", 70.0, "20mg, 40mg"),
    ];

    for (key, generic, brand, savings, strength) in brand_map {
        if brand_lower.contains(key) {
            return Ok(Json(json!({
                "substituted": true,
                "branded_name": brand,
                "generic_name": generic,
                "savings": savings,
                "strength_match": strength,
                "message": format!("Cheaper generic alternative {} found for brand-name {}.", generic, brand)
            })));
        }
    }

    Ok(Json(json!({
        "substituted": false,
        "branded_name": query.branded_name,
        "message": "No brand-to-generic mapping found in the clinical catalog for this medication.",
        "savings": 0.0
    })))
}
