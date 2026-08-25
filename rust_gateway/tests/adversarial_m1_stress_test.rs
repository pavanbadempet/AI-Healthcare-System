use base64::Engine as _;
use chrono::Utc;
use rust_gateway_ffi::db::crypto::{CryptoError, EncryptionService};
use rust_gateway_ffi::db::repo::{AppointmentRepo, UserRepo};
use rust_gateway_ffi::db::DbPool;
use rust_gateway_ffi::models::*;
use std::sync::Arc;

/// ------------------------------------------------------------------------------------------------
/// TEST SUITE 1: SQLite WAL Multi-Threaded Concurrency Stress Test
/// ------------------------------------------------------------------------------------------------
#[tokio::test]
async fn test_sqlite_wal_multi_threaded_concurrency_stress() {
    let db_path = format!("sqlite://./test_concurrency_{}.db", uuid::Uuid::new_v4());
    let pool = DbPool::new(&db_path)
        .await
        .expect("Failed to initialize SQLite WAL pool for concurrency stress");

    let pool_arc = Arc::new(pool);
    let num_tasks = 40;
    let mut handles = Vec::with_capacity(num_tasks);

    // Spawn 20 writer tasks and 20 reader tasks concurrently
    for i in 0..num_tasks {
        let pool = Arc::clone(&pool_arc);
        if i % 2 == 0 {
            // Writer task: creates users and appointments
            let handle = tokio::spawn(async move {
                let username = format!("stress_user_{}", i);
                let email = format!("user_{}@stress.test", i);
                let user_id = UserRepo::create_user(
                    &pool,
                    &username,
                    "hashed_pwd_stress_123",
                    "patient",
                    Some(&email),
                    Some(&format!("Stress User {}", i)),
                    None,
                )
                .await
                .expect("Concurrent UserRepo::create_user failed");

                assert!(user_id > 0);

                let appt_time = Utc::now().naive_utc();
                let appt_id = AppointmentRepo::create(
                    &pool,
                    None,
                    user_id,
                    None,
                    Some("General"),
                    appt_time,
                    Some("Stress checkup"),
                )
                .await
                .expect("Concurrent AppointmentRepo::create failed");

                assert!(appt_id > 0);
                (i, true)
            });
            handles.push(handle);
        } else {
            // Reader task: queries counts and users
            let handle = tokio::spawn(async move {
                // Short sleep to allow some writes to begin
                tokio::time::sleep(std::time::Duration::from_millis(5)).await;
                let sqlite = pool.as_sqlite().expect("Must have sqlite pool");
                let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
                    .fetch_one(sqlite)
                    .await
                    .expect("Concurrent SELECT COUNT(*) failed");
                assert!(count.0 >= 0);
                (i, false)
            });
            handles.push(handle);
        }
    }

    // Wait for all 40 concurrent workers to complete successfully
    for handle in handles {
        let result = handle.await.expect("Task panicked during concurrency run");
        assert!(result.0 < num_tasks);
    }

    // Verify final state consistency
    let sqlite = pool_arc.as_sqlite().unwrap();
    let final_user_count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
        .fetch_one(sqlite)
        .await
        .expect("Final user count query failed");

    // We spawned 20 writer tasks, so exactly 20 users must exist
    assert_eq!(final_user_count.0, 20);

    let final_appt_count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM appointments")
        .fetch_one(sqlite)
        .await
        .expect("Final appointment count query failed");
    assert_eq!(final_appt_count.0, 20);

    // Close pool and clean up test database file
    pool_arc.close().await;
    let clean_path = db_path.trim_start_matches("sqlite://");
    let _ = std::fs::remove_file(clean_path);
    let _ = std::fs::remove_file(format!("{}-wal", clean_path));
    let _ = std::fs::remove_file(format!("{}-shm", clean_path));
}

/// ------------------------------------------------------------------------------------------------
/// TEST SUITE 2: AES-256-GCM Cryptographic Boundary & Tampering Edge Cases
/// ------------------------------------------------------------------------------------------------
#[test]
fn test_aes_gcm_adversarial_tampering_and_edge_cases() {
    let key_str = "super_secure_pii_encryption_key_2026_test_32b";
    let crypto = EncryptionService::new(key_str);

    // 1. Empty string roundtrip
    let enc_empty = crypto.encrypt("").expect("Empty string encryption failed");
    assert!(!enc_empty.is_empty());
    let dec_empty = crypto.decrypt(&enc_empty).expect("Empty string decryption failed");
    assert_eq!(dec_empty, "");

    // 2. Whitespace and escape characters
    let whitespace_input = "  \t\n\r\n \0 leading and trailing with nulls \0 ";
    let enc_ws = crypto.encrypt(whitespace_input).expect("Whitespace enc failed");
    let dec_ws = crypto.decrypt(&enc_ws).expect("Whitespace dec failed");
    assert_eq!(dec_ws, whitespace_input);

    // 3. Multi-byte Unicode, Emoji, and International Healthcare Text
    let unicode_input = "Patient: 🩺 Dr. Ἀσκληπιός (Asklepios) — 診斷: 高血壓, 糖尿病. दवा: पैरासिटामोल 500mg. Status: 🟢 Stable.";
    let enc_uni = crypto.encrypt(unicode_input).expect("Unicode enc failed");
    let dec_uni = crypto.decrypt(&enc_uni).expect("Unicode dec failed");
    assert_eq!(dec_uni, unicode_input);

    // 4. Large Payload (1 MB buffer of realistic EHR JSON data)
    let large_json = format!(
        r#"{{"patient_id": 99999, "records": "{}", "notes": "{}"}}"#,
        "A".repeat(500_000),
        "B".repeat(500_000)
    );
    let enc_large = crypto.encrypt(&large_json).expect("Large payload enc failed");
    let dec_large = crypto.decrypt(&enc_large).expect("Large payload dec failed");
    assert_eq!(dec_large, large_json);

    // 5. Tampered Ciphertext Attack (Bit-flipping MUST cause authentication failure)
    let secret_message = "PATIENT_SSN: 999-00-1111; DIAGNOSIS: Stage 4 Malignancy";
    let valid_b64 = crypto.encrypt(secret_message).expect("Enc failed");
    let mut raw_bytes = base64::engine::general_purpose::STANDARD
        .decode(&valid_b64)
        .expect("Base64 decode failed");

    assert!(raw_bytes.len() > 16);
    // Flip a bit in the ciphertext payload (after the 12-byte nonce)
    let flip_idx = 15;
    raw_bytes[flip_idx] ^= 0xFF;
    let tampered_b64 = base64::engine::general_purpose::STANDARD.encode(&raw_bytes);

    let tamper_result = crypto.decrypt(&tampered_b64);
    assert!(
        tamper_result.is_err(),
        "Tampered ciphertext MUST fail AES-GCM tag verification"
    );
    match tamper_result {
        Err(CryptoError::DecryptionError(_)) => {}
        Err(other) => panic!("Expected DecryptionError on tampered data, got: {:?}", other),
        Ok(_) => panic!("Tampered ciphertext decrypted successfully! Fatal security vulnerability!"),
    }

    // 6. Truncated Payload (Less than 12-byte nonce)
    let short_payload = base64::engine::general_purpose::STANDARD.encode(b"short123");
    let short_result = crypto.decrypt(&short_payload);
    assert!(short_result.is_err());
    match short_result {
        Err(CryptoError::CiphertextTooShort) => {}
        Err(other) => panic!("Expected CiphertextTooShort, got: {:?}", other),
        Ok(_) => panic!("Short payload succeeded unexpectedly!"),
    }

    // 7. Malformed Base64 Strings
    assert!(crypto.decrypt("!@#$%^&*()").is_err());
    assert!(crypto.decrypt("invalid base64 with spaces").is_err());

    // 8. Key Segregation: Encryption with Key A cannot be decrypted with Key B
    let crypto_b = EncryptionService::new("completely_different_key_for_testing_0000");
    let enc_by_a = crypto.encrypt("Highly confidential clinical trial protocol").unwrap();
    let decrypt_by_b = crypto_b.decrypt(&enc_by_a);
    assert!(decrypt_by_b.is_err(), "Key B must fail to decrypt Key A ciphertext");

    // 9. Exact 32-byte Base64 key vs Arbitrary Secret string fallback
    let exact_32b_raw = [42u8; 32];
    let exact_32b_b64 = base64::engine::general_purpose::STANDARD.encode(exact_32b_raw);
    let crypto_exact = EncryptionService::new(&exact_32b_b64);
    let enc_exact = crypto_exact.encrypt("Exact key test").unwrap();
    assert_eq!(crypto_exact.decrypt(&enc_exact).unwrap(), "Exact key test");
}

/// ------------------------------------------------------------------------------------------------
/// TEST SUITE 3: Schema Constraints (Foreign Keys, Unique Constraints, Check Constraints, Cascades)
/// ------------------------------------------------------------------------------------------------
#[tokio::test]
async fn test_schema_constraints_and_foreign_keys() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite in-memory DbPool");

    let sqlite = pool.as_sqlite().unwrap();

    // 1. Verify Unique Constraint on users.username
    let u1 = UserRepo::create_user(
        &pool,
        "unique_doc",
        "hash1",
        "doctor",
        Some("doc1@test.com"),
        Some("Dr. Unique One"),
        None,
    )
    .await;
    assert!(u1.is_ok(), "First user creation should succeed");

    let u1_dup = UserRepo::create_user(
        &pool,
        "unique_doc", // DUPLICATE USERNAME
        "hash2",
        "doctor",
        Some("doc2@test.com"),
        Some("Dr. Unique Two"),
        None,
    )
    .await;
    assert!(
        u1_dup.is_err(),
        "Duplicate username must be rejected by UNIQUE constraint"
    );

    // 2. Verify Unique Constraint on users.email
    let u2_dup_email = UserRepo::create_user(
        &pool,
        "unique_doc_2",
        "hash3",
        "doctor",
        Some("doc1@test.com"), // DUPLICATE EMAIL
        Some("Dr. Unique Three"),
        None,
    )
    .await;
    assert!(
        u2_dup_email.is_err(),
        "Duplicate email must be rejected by UNIQUE constraint"
    );

    // 3. Verify Foreign Key Constraint Enforcement: Non-existent facility_id
    let invalid_dept_res = sqlx::query(
        "INSERT INTO departments (facility_id, name, department_type) VALUES (?, ?, ?)"
    )
    .bind(999999) // Non-existent facility_id
    .bind("Orphan Cardiology")
    .bind("OPD")
    .execute(sqlite)
    .await;

    assert!(
        invalid_dept_res.is_err(),
        "Foreign key violation on facility_id MUST return an error"
    );

    // 4. Verify Foreign Key Constraint on Appointments: Non-existent user_id
    let invalid_appt_res = sqlx::query(
        "INSERT INTO appointments (user_id, status) VALUES (?, ?)"
    )
    .bind(888888) // Non-existent user_id
    .bind("Scheduled")
    .execute(sqlite)
    .await;

    assert!(
        invalid_appt_res.is_err(),
        "Foreign key violation on user_id MUST return an error"
    );

    // 5. Verify Check Constraint on users.role
    let invalid_role_res = sqlx::query(
        "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)"
    )
    .bind("hacker_user")
    .bind("hash_secret")
    .bind("unauthorized_superadmin") // INVALID ROLE
    .execute(sqlite)
    .await;

    assert!(
        invalid_role_res.is_err(),
        "Check constraint on users.role MUST reject invalid role values"
    );

    // 6. Verify Check Constraint on appointments.status
    let valid_user_id = u1.unwrap();
    let invalid_appt_status_res = sqlx::query(
        "INSERT INTO appointments (user_id, status) VALUES (?, ?)"
    )
    .bind(valid_user_id)
    .bind("InvalidStatusXYZ") // INVALID STATUS
    .execute(sqlite)
    .await;

    assert!(
        invalid_appt_status_res.is_err(),
        "Check constraint on appointments.status MUST reject invalid status"
    );

    // 7. Verify Check Constraint on health_records.record_type
    let invalid_hr_res = sqlx::query(
        "INSERT INTO health_records (user_id, record_type, data) VALUES (?, ?, ?)"
    )
    .bind(valid_user_id)
    .bind("unsupported_disease_type") // INVALID RECORD TYPE
    .bind("{}")
    .execute(sqlite)
    .await;

    assert!(
        invalid_hr_res.is_err(),
        "Check constraint on health_records.record_type MUST reject unsupported types"
    );

    // 8. Verify CASCADE Delete on InvoiceLineItems
    let inv_id: (i64,) = sqlx::query_as(
        "INSERT INTO invoices (patient_id, total_amount, currency) VALUES (?, ?, ?) RETURNING id"
    )
    .bind(valid_user_id)
    .bind(1000.0)
    .bind("INR")
    .fetch_one(sqlite)
    .await
    .expect("Insert invoice failed");

    sqlx::query(
        "INSERT INTO invoice_line_items (invoice_id, description, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?)"
    )
    .bind(inv_id.0)
    .bind("Consultation Fee")
    .bind(1.0)
    .bind(1000.0)
    .bind(1000.0)
    .execute(sqlite)
    .await
    .expect("Insert line item failed");

    // Confirm line item exists
    let item_count_before: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM invoice_line_items WHERE invoice_id = ?"
    )
    .bind(inv_id.0)
    .fetch_one(sqlite)
    .await
    .unwrap();
    assert_eq!(item_count_before.0, 1);

    // Delete parent invoice
    sqlx::query("DELETE FROM invoices WHERE id = ?")
        .bind(inv_id.0)
        .execute(sqlite)
        .await
        .expect("Delete invoice failed");

    // Confirm child line item was cascade deleted
    let item_count_after: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM invoice_line_items WHERE invoice_id = ?"
    )
    .bind(inv_id.0)
    .fetch_one(sqlite)
    .await
    .unwrap();
    assert_eq!(
        item_count_after.0, 0,
        "Child invoice_line_items MUST be cascade deleted when invoice is deleted"
    );
}

/// ------------------------------------------------------------------------------------------------
/// TEST SUITE 4: Optional Field Nullability and Model Deserialization Verification
/// ------------------------------------------------------------------------------------------------
#[tokio::test]
async fn test_optional_field_nullability_and_full_deserialization() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite in-memory DbPool");

    let sqlite = pool.as_sqlite().unwrap();

    // 1. Insert User with absolute minimal required fields (all optionals NULL)
    let user_id: (i64,) = sqlx::query_as(
        "INSERT INTO users (username, hashed_password) VALUES (?, ?) RETURNING id"
    )
    .bind("minimalist_user")
    .bind("minimal_hash")
    .fetch_one(sqlite)
    .await
    .expect("Failed to insert minimal user");

    let user: User = sqlx::query_as("SELECT * FROM users WHERE id = ?")
        .bind(user_id.0)
        .fetch_one(sqlite)
        .await
        .expect("Failed to deserialize User with NULL optionals");

    assert_eq!(user.username, "minimalist_user");
    assert_eq!(user.role, "patient");
    assert!(user.email.is_none());
    assert!(user.full_name.is_none());
    assert!(user.dob.is_none());
    assert!(user.height.is_none());
    assert!(user.weight.is_none());
    assert_eq!(user.is_deleted, 0);

    // 2. Insert VitalObservation with only patient_id (all vitals NULL)
    let vital_insert: (i64,) = sqlx::query_as(
        "INSERT INTO vital_observations (patient_id, source) VALUES (?, ?) RETURNING id"
    )
    .bind(user_id.0)
    .bind("test")
    .fetch_one(sqlite)
    .await
    .expect("Insert minimal vital");

    let vital: VitalObservation = sqlx::query_as("SELECT * FROM vital_observations WHERE id = ?")
        .bind(vital_insert.0)
        .fetch_one(sqlite)
        .await
        .expect("Failed to deserialize VitalObservation with NULL metrics");

    assert_eq!(vital.patient_id, user_id.0);
    assert!(vital.heart_rate.is_none());
    assert!(vital.systolic_bp.is_none());
    assert!(vital.diastolic_bp.is_none());
    assert!(vital.spo2.is_none());

    // 3. Test Transaction Rollback
    let mut tx = sqlite.begin().await.expect("Begin transaction failed");
    sqlx::query("INSERT INTO users (username, hashed_password) VALUES (?, ?)")
        .bind("tx_user_should_rollback")
        .bind("tx_hash")
        .execute(&mut *tx)
        .await
        .expect("Insert in tx");

    // Intentionally roll back
    tx.rollback().await.expect("Rollback failed");

    let rolled_back_user = UserRepo::find_by_username(&pool, "tx_user_should_rollback")
        .await
        .expect("Query failed");
    assert!(
        rolled_back_user.is_none(),
        "User inserted inside rolled-back transaction MUST NOT exist"
    );
}
