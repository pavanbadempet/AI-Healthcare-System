use crate::db::DbPool;
use crate::models::*;
use chrono::{NaiveDateTime, Utc};
use sqlx::Error;

// ============================================================================
// 1. User Repository
// ============================================================================
pub struct UserRepo;

impl UserRepo {
    pub async fn find_by_id(pool: &DbPool, id: i64) -> Result<Option<User>, Error> {
        let sql = "SELECT * FROM users WHERE id = $1 AND is_deleted = 0";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, User>(sql).bind(id).fetch_optional(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, User>(sql).bind(id).fetch_optional(p).await,
        }
    }

    pub async fn find_by_username(pool: &DbPool, username: &str) -> Result<Option<User>, Error> {
        let sql = "SELECT * FROM users WHERE username = $1 AND is_deleted = 0";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, User>(sql).bind(username).fetch_optional(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, User>(sql).bind(username).fetch_optional(p).await,
        }
    }

    pub async fn create_user(
        pool: &DbPool,
        username: &str,
        hashed_password: &str,
        role: &str,
        email: Option<&str>,
        full_name: Option<&str>,
        facility_id: Option<i64>,
    ) -> Result<i64, Error> {
        let sql = r#"
            INSERT INTO users (username, hashed_password, role, email, full_name, facility_id, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        "#;
        let now = Utc::now().naive_utc();
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(username)
                    .bind(hashed_password)
                    .bind(role)
                    .bind(email)
                    .bind(full_name)
                    .bind(facility_id)
                    .bind(now)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO users (username, hashed_password, role, email, full_name, facility_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    "#
                )
                .bind(username)
                .bind(hashed_password)
                .bind(role)
                .bind(email)
                .bind(full_name)
                .bind(facility_id)
                .bind(now)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn soft_delete(pool: &DbPool, user_id: i64) -> Result<bool, Error> {
        let now = Utc::now().naive_utc();
        let sql = "UPDATE users SET is_deleted = 1, deleted_at = $1 WHERE id = $2";
        let affected = match pool {
            DbPool::Sqlite(p) => sqlx::query(sql).bind(now).bind(user_id).execute(p).await?.rows_affected(),
            DbPool::Postgres(p) => sqlx::query(sql).bind(now).bind(user_id).execute(p).await?.rows_affected(),
        };
        Ok(affected > 0)
    }
}

// ============================================================================
// 2. Appointment Repository
// ============================================================================
pub struct AppointmentRepo;

impl AppointmentRepo {
    pub async fn find_by_id(pool: &DbPool, id: i64) -> Result<Option<Appointment>, Error> {
        let sql = "SELECT * FROM appointments WHERE id = $1 AND is_deleted = 0";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, Appointment>(sql).bind(id).fetch_optional(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, Appointment>(sql).bind(id).fetch_optional(p).await,
        }
    }

    pub async fn list_for_user(pool: &DbPool, user_id: i64) -> Result<Vec<Appointment>, Error> {
        let sql = "SELECT * FROM appointments WHERE user_id = $1 AND is_deleted = 0 ORDER BY date_time ASC";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, Appointment>(sql).bind(user_id).fetch_all(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, Appointment>(sql).bind(user_id).fetch_all(p).await,
        }
    }

    pub async fn list_for_doctor(pool: &DbPool, doctor_id: i64) -> Result<Vec<Appointment>, Error> {
        let sql = "SELECT * FROM appointments WHERE doctor_id = $1 AND is_deleted = 0 ORDER BY date_time ASC";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, Appointment>(sql).bind(doctor_id).fetch_all(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, Appointment>(sql).bind(doctor_id).fetch_all(p).await,
        }
    }

    pub async fn create(
        pool: &DbPool,
        facility_id: Option<i64>,
        user_id: i64,
        doctor_id: Option<i64>,
        specialist: Option<&str>,
        date_time: NaiveDateTime,
        reason: Option<&str>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql_insert = r#"
            INSERT INTO appointments (facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted)
            VALUES ($1, $2, $3, $4, $5, $6, 'Scheduled', $7, 0)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql_insert)
                    .bind(facility_id)
                    .bind(user_id)
                    .bind(doctor_id)
                    .bind(specialist)
                    .bind(date_time)
                    .bind(reason)
                    .bind(now)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO appointments (facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted)
                    VALUES ($1, $2, $3, $4, $5, $6, 'Scheduled', $7, 0)
                    RETURNING id
                    "#
                )
                .bind(facility_id)
                .bind(user_id)
                .bind(doctor_id)
                .bind(specialist)
                .bind(date_time)
                .bind(reason)
                .bind(now)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn update_status(pool: &DbPool, appointment_id: i64, status: &str) -> Result<bool, Error> {
        let sql = "UPDATE appointments SET status = $1 WHERE id = $2 AND is_deleted = 0";
        let affected = match pool {
            DbPool::Sqlite(p) => sqlx::query(sql).bind(status).bind(appointment_id).execute(p).await?.rows_affected(),
            DbPool::Postgres(p) => sqlx::query(sql).bind(status).bind(appointment_id).execute(p).await?.rows_affected(),
        };
        Ok(affected > 0)
    }

    pub async fn reschedule(pool: &DbPool, appointment_id: i64, new_dt: NaiveDateTime) -> Result<bool, Error> {
        let sql = "UPDATE appointments SET date_time = $1, status = 'Rescheduled' WHERE id = $2 AND is_deleted = 0";
        let affected = match pool {
            DbPool::Sqlite(p) => sqlx::query(sql).bind(new_dt).bind(appointment_id).execute(p).await?.rows_affected(),
            DbPool::Postgres(p) => sqlx::query(sql).bind(new_dt).bind(appointment_id).execute(p).await?.rows_affected(),
        };
        Ok(affected > 0)
    }
}

// ============================================================================
// 3. Clinical & Vitals Repository
// ============================================================================
pub struct VitalObservationRepo;

impl VitalObservationRepo {
    pub async fn record(
        pool: &DbPool,
        facility_id: Option<i64>,
        patient_id: i64,
        recorded_by_id: Option<i64>,
        encounter_id: Option<i64>,
        department_id: Option<i64>,
        source: &str,
        heart_rate: Option<f64>,
        systolic_bp: Option<f64>,
        diastolic_bp: Option<f64>,
        spo2: Option<f64>,
        temperature_c: Option<f64>,
        respiratory_rate: Option<f64>,
        blood_glucose: Option<f64>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = r#"
            INSERT INTO vital_observations (
                facility_id, patient_id, recorded_by_id, encounter_id, department_id,
                source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c,
                respiratory_rate, blood_glucose, observed_at, created_at, is_deleted
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 0)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(facility_id)
                    .bind(patient_id)
                    .bind(recorded_by_id)
                    .bind(encounter_id)
                    .bind(department_id)
                    .bind(source)
                    .bind(heart_rate)
                    .bind(systolic_bp)
                    .bind(diastolic_bp)
                    .bind(spo2)
                    .bind(temperature_c)
                    .bind(respiratory_rate)
                    .bind(blood_glucose)
                    .bind(now)
                    .bind(now)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO vital_observations (
                        facility_id, patient_id, recorded_by_id, encounter_id, department_id,
                        source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c,
                        respiratory_rate, blood_glucose, observed_at, created_at, is_deleted
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 0)
                    RETURNING id
                    "#
                )
                .bind(facility_id)
                .bind(patient_id)
                .bind(recorded_by_id)
                .bind(encounter_id)
                .bind(department_id)
                .bind(source)
                .bind(heart_rate)
                .bind(systolic_bp)
                .bind(diastolic_bp)
                .bind(spo2)
                .bind(temperature_c)
                .bind(respiratory_rate)
                .bind(blood_glucose)
                .bind(now)
                .bind(now)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn get_latest(pool: &DbPool, patient_id: i64) -> Result<Option<VitalObservation>, Error> {
        let sql = "SELECT * FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 1";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).fetch_optional(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).fetch_optional(p).await,
        }
    }

    pub async fn find_by_patient_id(pool: &DbPool, patient_id: i64, limit: i64) -> Result<Vec<VitalObservation>, Error> {
        let sql = "SELECT * FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT $2";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).bind(limit).fetch_all(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).bind(limit).fetch_all(p).await,
        }
    }
}

// ============================================================================
// 4. Hospital Facilities & Operations Repository
// ============================================================================
pub struct HospitalRepo;

impl HospitalRepo {
    pub async fn create_facility(
        pool: &DbPool,
        name: &str,
        facility_type: &str,
        country: Option<&str>,
        region: Option<&str>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = "INSERT INTO hospital_facilities (name, facility_type, country, region, status, created_at) VALUES ($1, $2, $3, $4, 'active', $5)";
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(name)
                    .bind(facility_type)
                    .bind(country)
                    .bind(region)
                    .bind(now)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    "INSERT INTO hospital_facilities (name, facility_type, country, region, status, created_at) VALUES ($1, $2, $3, $4, 'active', $5) RETURNING id"
                )
                .bind(name)
                .bind(facility_type)
                .bind(country)
                .bind(region)
                .bind(now)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn list_facilities(pool: &DbPool) -> Result<Vec<HospitalFacility>, Error> {
        let sql = "SELECT * FROM hospital_facilities WHERE status = 'active' ORDER BY name ASC";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, HospitalFacility>(sql).fetch_all(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, HospitalFacility>(sql).fetch_all(p).await,
        }
    }
}

// ============================================================================
// 5. Billing & Invoice Repository
// ============================================================================
pub struct BillingRepo;

impl BillingRepo {
    pub async fn create_invoice(
        pool: &DbPool,
        facility_id: Option<i64>,
        patient_id: i64,
        encounter_id: Option<i64>,
        admission_id: Option<i64>,
        created_by_id: Option<i64>,
        subtotal: f64,
        discount: f64,
        tax: f64,
        total: f64,
        currency: &str,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = r#"
            INSERT INTO invoices (
                facility_id, patient_id, encounter_id, admission_id, created_by_id,
                status, subtotal, discount_amount, tax_amount, total_amount,
                paid_amount, balance_amount, currency, created_at, issued_at
            ) VALUES ($1, $2, $3, $4, $5, 'issued', $6, $7, $8, $9, 0, $9, $10, $11, $11)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(facility_id)
                    .bind(patient_id)
                    .bind(encounter_id)
                    .bind(admission_id)
                    .bind(created_by_id)
                    .bind(subtotal)
                    .bind(discount)
                    .bind(tax)
                    .bind(total)
                    .bind(currency)
                    .bind(now)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO invoices (
                        facility_id, patient_id, encounter_id, admission_id, created_by_id,
                        status, subtotal, discount_amount, tax_amount, total_amount,
                        paid_amount, balance_amount, currency, created_at, issued_at
                    ) VALUES ($1, $2, $3, $4, $5, 'issued', $6, $7, $8, $9, 0, $9, $10, $11, $11)
                    RETURNING id
                    "#
                )
                .bind(facility_id)
                .bind(patient_id)
                .bind(encounter_id)
                .bind(admission_id)
                .bind(created_by_id)
                .bind(subtotal)
                .bind(discount)
                .bind(tax)
                .bind(total)
                .bind(currency)
                .bind(now)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn record_payment(
        pool: &DbPool,
        facility_id: Option<i64>,
        invoice_id: i64,
        patient_id: i64,
        collected_by_id: Option<i64>,
        amount: f64,
        payment_method: &str,
        reference_id: Option<&str>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = r#"
            INSERT INTO billing_payments (
                facility_id, invoice_id, patient_id, collected_by_id,
                amount, payment_method, reference_id, status, collected_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'collected', $8)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(facility_id)
                    .bind(invoice_id)
                    .bind(patient_id)
                    .bind(collected_by_id)
                    .bind(amount)
                    .bind(payment_method)
                    .bind(reference_id)
                    .bind(now)
                    .execute(p)
                    .await?;
                // Update invoice paid & balance
                let _ = sqlx::query(
                    "UPDATE invoices SET paid_amount = paid_amount + $1, balance_amount = total_amount - (paid_amount + $1) WHERE id = $2"
                )
                .bind(amount)
                .bind(invoice_id)
                .execute(p)
                .await;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO billing_payments (
                        facility_id, invoice_id, patient_id, collected_by_id,
                        amount, payment_method, reference_id, status, collected_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'collected', $8)
                    RETURNING id
                    "#
                )
                .bind(facility_id)
                .bind(invoice_id)
                .bind(patient_id)
                .bind(collected_by_id)
                .bind(amount)
                .bind(payment_method)
                .bind(reference_id)
                .bind(now)
                .fetch_one(p)
                .await?;
                // Update invoice paid & balance
                let _ = sqlx::query(
                    "UPDATE invoices SET paid_amount = paid_amount + $1, balance_amount = total_amount - (paid_amount + $1) WHERE id = $2"
                )
                .bind(amount)
                .bind(invoice_id)
                .execute(p)
                .await;
                Ok(row.0)
            }
        }
    }
}

// ============================================================================
// 6. Consent Repository
// ============================================================================
pub struct ConsentRepo;

impl ConsentRepo {
    pub async fn accept_eula(
        pool: &DbPool,
        user_id: i64,
        eula_version: &str,
        ip_address: Option<&str>,
        user_agent: Option<&str>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = r#"
            INSERT INTO consent_records (user_id, eula_version, accepted_at, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(user_id)
                    .bind(eula_version)
                    .bind(now)
                    .bind(ip_address)
                    .bind(user_agent)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO consent_records (user_id, eula_version, accepted_at, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    "#
                )
                .bind(user_id)
                .bind(eula_version)
                .bind(now)
                .bind(ip_address)
                .bind(user_agent)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn get_latest_consent(pool: &DbPool, user_id: i64) -> Result<Option<ConsentRecord>, Error> {
        let sql = "SELECT * FROM consent_records WHERE user_id = $1 ORDER BY accepted_at DESC LIMIT 1";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, ConsentRecord>(sql).bind(user_id).fetch_optional(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, ConsentRecord>(sql).bind(user_id).fetch_optional(p).await,
        }
    }
}

// ============================================================================
// 7. Audit Log Repository
// ============================================================================
pub struct AuditRepo;

impl AuditRepo {
    pub async fn log(
        pool: &DbPool,
        facility_id: Option<i64>,
        admin_id: i64,
        target_user_id: Option<i64>,
        action: &str,
        details: Option<&str>,
    ) -> Result<i64, Error> {
        let now = Utc::now().naive_utc();
        let sql = r#"
            INSERT INTO audit_logs (facility_id, admin_id, target_user_id, action, timestamp, details, is_deleted)
            VALUES ($1, $2, $3, $4, $5, $6, 0)
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let res = sqlx::query(sql)
                    .bind(facility_id)
                    .bind(admin_id)
                    .bind(target_user_id)
                    .bind(action)
                    .bind(now)
                    .bind(details)
                    .execute(p)
                    .await?;
                Ok(res.last_insert_rowid())
            }
            DbPool::Postgres(p) => {
                let row: (i64,) = sqlx::query_as(
                    r#"
                    INSERT INTO audit_logs (facility_id, admin_id, target_user_id, action, timestamp, details, is_deleted)
                    VALUES ($1, $2, $3, $4, $5, $6, 0)
                    RETURNING id
                    "#
                )
                .bind(facility_id)
                .bind(admin_id)
                .bind(target_user_id)
                .bind(action)
                .bind(now)
                .bind(details)
                .fetch_one(p)
                .await?;
                Ok(row.0)
            }
        }
    }

    pub async fn find_recent(pool: &DbPool, limit: i64) -> Result<Vec<AuditLog>, Error> {
        let sql = "SELECT * FROM audit_logs WHERE is_deleted = 0 ORDER BY timestamp DESC LIMIT $1";
        match pool {
            DbPool::Sqlite(p) => sqlx::query_as::<_, AuditLog>(sql).bind(limit).fetch_all(p).await,
            DbPool::Postgres(p) => sqlx::query_as::<_, AuditLog>(sql).bind(limit).fetch_all(p).await,
        }
    }
}
