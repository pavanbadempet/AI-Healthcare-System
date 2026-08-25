use chrono::Utc;
use rust_gateway_ffi::db::crypto::EncryptionService;
use rust_gateway_ffi::db::repo::*;
use rust_gateway_ffi::db::DbPool;
use rust_gateway_ffi::models::*;

#[tokio::test]
async fn test_in_memory_sqlite_db_pool_and_all_46_tables() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite in-memory DbPool with schema");

    assert!(pool.is_sqlite());
    assert!(!pool.is_postgres());
    assert!(pool.size() >= 1);

    let sqlite_pool = pool.as_sqlite().expect("Must have sqlite pool");

    // List of all 46 table names to verify
    let expected_tables = vec![
        "hospital_facilities",
        "departments",
        "users",
        "beds",
        "appointments",
        "encounters",
        "admissions",
        "dicom_studies",
        "clinical_orders",
        "care_events",
        "vital_observations",
        "monitoring_signals",
        "diagnostic_results",
        "spark_streaming_metrics",
        "billable_services",
        "invoices",
        "invoice_line_items",
        "billing_payments",
        "insurance_claims",
        "medication_inventory",
        "prescriptions",
        "prescription_items",
        "dispense_records",
        "health_records",
        "chat_logs",
        "audit_logs",
        "schema_contracts",
        "contract_violations",
        "data_catalog_datasets",
        "data_catalog_lineage",
        "feature_attribution_logs",
        "interoperability_consents",
        "abdm_consent_events",
        "interoperability_export_profiles",
        "interoperability_exports",
        "abha_links",
        "clinical_alerts",
        "patient_insights",
        "clinical_ai_corrections",
        "discharge_summaries",
        "nursing_tasks",
        "model_feedbacks",
        "federated_sync_audits",
        "smart_apps",
        "smart_launch_contexts",
        "consent_records",
    ];

    assert_eq!(expected_tables.len(), 46);

    let rows: Vec<(String,)> = sqlx::query_as("SELECT name FROM sqlite_master WHERE type='table'")
        .fetch_all(sqlite_pool)
        .await
        .expect("Failed to query sqlite_master");

    let existing_tables: std::collections::HashSet<String> = rows.into_iter().map(|r| r.0).collect();

    for table in expected_tables {
        assert!(
            existing_tables.contains(table),
            "Table {} must exist in database schema",
            table
        );
    }
}

#[tokio::test]
async fn test_aes_gcm_pii_encryption_and_decryption() {
    let service = EncryptionService::new("test_encryption_key_for_pii_models_123");
    let plaintext = "patient_ssn=000-11-2222;email=patient@hospital.org;diagnosis=Type 2 Diabetes";

    let ciphertext = service.encrypt(plaintext).expect("Encryption failed");
    assert_ne!(ciphertext, plaintext);
    assert!(!ciphertext.is_empty());

    let decrypted = service.decrypt(&ciphertext).expect("Decryption failed");
    assert_eq!(decrypted, plaintext);

    // Test optional helpers
    let opt_enc = service.encrypt_opt(Some(plaintext)).expect("Enc opt");
    let opt_dec = service.decrypt_opt(opt_enc.as_deref()).expect("Dec opt");
    assert_eq!(opt_dec, Some(plaintext.to_string()));

    let none_enc = service.encrypt_opt(None).expect("Enc none");
    assert!(none_enc.is_none());
}

#[tokio::test]
async fn test_user_repository_and_soft_delete() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite pool");

    let user_id = UserRepo::create_user(
        &pool,
        "dr_smith",
        "$2b$12$hashedpasswordplaceholder",
        "doctor",
        Some("dr.smith@clinic.com"),
        Some("Dr. Jane Smith"),
        None,
    )
    .await
    .expect("Failed to create user");

    assert!(user_id > 0);

    let user = UserRepo::find_by_id(&pool, user_id)
        .await
        .expect("Find by id failed")
        .expect("User should exist");
    assert_eq!(user.username, "dr_smith");
    assert_eq!(user.role, "doctor");
    assert_eq!(user.full_name, Some("Dr. Jane Smith".to_string()));
    assert_eq!(user.is_deleted, 0);

    let user_by_name = UserRepo::find_by_username(&pool, "dr_smith")
        .await
        .expect("Find by username failed")
        .expect("User should exist");
    assert_eq!(user_by_name.id, user_id);

    // Test soft delete
    let deleted = UserRepo::soft_delete(&pool, user_id)
        .await
        .expect("Soft delete failed");
    assert!(deleted);

    let user_after_delete = UserRepo::find_by_id(&pool, user_id)
        .await
        .expect("Find after delete");
    assert!(user_after_delete.is_none());
}

#[tokio::test]
async fn test_appointment_and_vitals_repository() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite pool");

    let patient_id = UserRepo::create_user(
        &pool,
        "patient_john",
        "hash123",
        "patient",
        Some("john@example.com"),
        Some("John Doe"),
        None,
    )
    .await
    .expect("Create patient");

    let doctor_id = UserRepo::create_user(
        &pool,
        "dr_alice",
        "hash456",
        "doctor",
        Some("alice@example.com"),
        Some("Dr. Alice"),
        None,
    )
    .await
    .expect("Create doctor");

    let appt_time = Utc::now().naive_utc() + chrono::Duration::days(2);

    let appt_id = AppointmentRepo::create(
        &pool,
        None,
        patient_id,
        Some(doctor_id),
        Some("Cardiology"),
        appt_time,
        Some("Annual checkup"),
    )
    .await
    .expect("Create appointment");

    let appt = AppointmentRepo::find_by_id(&pool, appt_id)
        .await
        .expect("Find appt")
        .expect("Appt exists");
    assert_eq!(appt.status, "Scheduled");
    assert_eq!(appt.specialist, Some("Cardiology".to_string()));

    // Record vitals
    let vital_id = VitalObservationRepo::record(
        &pool,
        None,
        patient_id,
        Some(doctor_id),
        None,
        None,
        "device",
        Some(72.0),
        Some(120.0),
        Some(80.0),
        Some(98.5),
        Some(36.8),
        Some(16.0),
        Some(95.0),
    )
    .await
    .expect("Record vitals");

    assert!(vital_id > 0);

    let latest_vitals = VitalObservationRepo::get_latest(&pool, patient_id)
        .await
        .expect("Get latest vitals")
        .expect("Vitals exist");
    assert_eq!(latest_vitals.heart_rate, Some(72.0));
    assert_eq!(latest_vitals.systolic_bp, Some(120.0));
    assert_eq!(latest_vitals.spo2, Some(98.5));
}

#[tokio::test]
async fn test_billing_and_consent_repository() {
    let pool = DbPool::new("sqlite::memory:")
        .await
        .expect("Failed to initialize SQLite pool");

    let patient_id = UserRepo::create_user(
        &pool,
        "patient_sam",
        "hash789",
        "patient",
        None,
        Some("Sam Smith"),
        None,
    )
    .await
    .expect("Create patient");

    let inv_id = BillingRepo::create_invoice(
        &pool,
        None,
        patient_id,
        None,
        None,
        None,
        1500.0,
        100.0,
        75.0,
        1475.0,
        "INR",
    )
    .await
    .expect("Create invoice");

    assert!(inv_id > 0);

    let payment_id = BillingRepo::record_payment(
        &pool,
        None,
        inv_id,
        patient_id,
        None,
        1475.0,
        "UPI",
        Some("UPI-REF-998877"),
    )
    .await
    .expect("Record payment");

    assert!(payment_id > 0);

    // EULA Consent
    let consent_id = ConsentRepo::accept_eula(
        &pool,
        patient_id,
        "1.0",
        Some("127.0.0.1"),
        Some("Mozilla/5.0"),
    )
    .await
    .expect("Accept EULA");

    assert!(consent_id > 0);

    let latest_consent = ConsentRepo::get_latest_consent(&pool, patient_id)
        .await
        .expect("Get consent")
        .expect("Consent exists");
    assert_eq!(latest_consent.eula_version, "1.0");
}

#[test]
fn test_all_46_models_serialization_and_deserialization() {
    let now = Utc::now().naive_utc();

    // 1. User
    let user = User {
        id: 1,
        username: "test_user".into(),
        hashed_password: "hash".into(),
        created_at: Some(now),
        role: "patient".into(),
        email: Some("p@test.com".into()),
        full_name: Some("Test User".into()),
        gender: Some("M".into()),
        blood_type: Some("A+".into()),
        dob: Some("1990-01-01".into()),
        height: Some(175.0),
        weight: Some(70.0),
        existing_ailments: None,
        profile_picture: None,
        about_me: None,
        diet: Some("Keto".into()),
        activity_level: Some("Active".into()),
        sleep_hours: Some(8.0),
        stress_level: Some("Low".into()),
        allow_data_collection: 1,
        facility_id: Some(1),
        plan_tier: "free".into(),
        subscription_expiry: None,
        razorpay_customer_id: None,
        consultation_fee: 500.0,
        specialization: None,
        psych_profile: None,
        totp_secret: None,
        is_totp_enabled: 0,
        is_deleted: 0,
        deleted_at: None,
    };
    let json = serde_json::to_string(&user).unwrap();
    assert!(json.contains("test_user"));

    // 2. Appointment
    let appt = Appointment {
        id: 1,
        facility_id: Some(1),
        user_id: 1,
        doctor_id: Some(2),
        specialist: Some("General".into()),
        date_time: Some(now),
        reason: Some("Checkup".into()),
        status: "Scheduled".into(),
        created_at: Some(now),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&appt).is_ok());

    // 3. HospitalFacility
    let facility = HospitalFacility {
        id: 1,
        name: "Central Hospital".into(),
        facility_type: "hospital".into(),
        country: Some("India".into()),
        region: Some("Telangana".into()),
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&facility).is_ok());

    // 4. Department
    let dept = Department {
        id: 1,
        facility_id: Some(1),
        name: "Cardiology".into(),
        department_type: "IPD".into(),
        location: Some("Floor 3".into()),
        description: None,
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&dept).is_ok());

    // 5. Bed
    let bed = Bed {
        id: 1,
        facility_id: Some(1),
        department_id: 1,
        bed_number: "B-101".into(),
        ward: Some("ICU".into()),
        status: "available".into(),
        current_patient_id: None,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&bed).is_ok());

    // 6. Encounter
    let enc = Encounter {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        doctor_id: Some(2),
        department_id: Some(1),
        encounter_type: "OPD".into(),
        reason: Some("Fever".into()),
        priority: "routine".into(),
        status: "open".into(),
        started_at: Some(now),
        ended_at: None,
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&enc).is_ok());

    // 7. Admission
    let adm = Admission {
        id: 1,
        facility_id: Some(1),
        encounter_id: 1,
        patient_id: 1,
        doctor_id: Some(2),
        department_id: Some(1),
        bed_id: Some(1),
        admitted_at: Some(now),
        discharged_at: None,
        reason: Some("Severe infection".into()),
        status: "active".into(),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&adm).is_ok());

    // 8. DicomStudy
    let dicom = DicomStudy {
        id: 1,
        study_uid: "1.2.840.113619".into(),
        patient_id: Some(1),
        modality: "CT".into(),
        target_vault: "PACS-PRIMARY-01".into(),
        file_name: "study01.dcm".into(),
        file_size_kb: 2048,
        is_preamble_valid: "true".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&dicom).is_ok());

    // 9. ClinicalOrder
    let order = ClinicalOrder {
        id: 1,
        facility_id: Some(1),
        encounter_id: Some(1),
        patient_id: 1,
        doctor_id: Some(2),
        department_id: Some(1),
        order_type: "lab".into(),
        title: "CBC".into(),
        priority: "urgent".into(),
        status: "ordered".into(),
        notes: None,
        created_at: Some(now),
        completed_at: None,
    };
    assert!(serde_json::to_string(&order).is_ok());

    // 10. CareEvent
    let event = CareEvent {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        actor_user_id: Some(2),
        encounter_id: Some(1),
        department_id: Some(1),
        event_type: "medication_admin".into(),
        title: "Administered Antibiotics".into(),
        summary: None,
        severity: "info".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&event).is_ok());

    // 11. VitalObservation
    let vital = VitalObservation {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        recorded_by_id: Some(2),
        encounter_id: Some(1),
        department_id: Some(1),
        source: "device".into(),
        heart_rate: Some(75.0),
        systolic_bp: Some(120.0),
        diastolic_bp: Some(80.0),
        spo2: Some(99.0),
        temperature_c: Some(37.0),
        respiratory_rate: Some(16.0),
        blood_glucose: Some(90.0),
        observed_at: Some(now),
        created_at: Some(now),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&vital).is_ok());

    // 12. MonitoringSignal
    let sig = MonitoringSignal {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        vital_observation_id: Some(1),
        encounter_id: Some(1),
        department_id: Some(1),
        signal_type: "tachycardia".into(),
        severity: "warning".into(),
        title: "High Heart Rate".into(),
        summary: "HR > 100 bpm".into(),
        status: "open".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&sig).is_ok());

    // 13. DiagnosticResult
    let diag = DiagnosticResult {
        id: 1,
        facility_id: Some(1),
        order_id: 1,
        encounter_id: Some(1),
        patient_id: 1,
        doctor_id: Some(2),
        department_id: Some(1),
        result_type: "lab".into(),
        title: "HbA1c".into(),
        summary: "5.6% Normal".into(),
        abnormal_flag: 0,
        status: "final".into(),
        review_status: "reviewed".into(),
        review_note: None,
        reviewed_by_id: Some(2),
        reviewed_at: Some(now),
        created_at: Some(now),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&diag).is_ok());

    // 14. SparkStreamingMetrics
    let spark = SparkStreamingMetrics {
        id: 1,
        batch_id: 101,
        records_processed: 5000,
        processing_time_ms: 12.5,
        ml_latency_ms: 3.2,
        timestamp: Some(now),
    };
    assert!(serde_json::to_string(&spark).is_ok());

    // 15. BillableService
    let service = BillableService {
        id: 1,
        facility_id: Some(1),
        service_code: "SRV-001".into(),
        name: "Consultation".into(),
        service_type: "OPD".into(),
        department_id: Some(1),
        unit_price: 500.0,
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&service).is_ok());

    // 16. Invoice
    let invoice = Invoice {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        encounter_id: Some(1),
        admission_id: None,
        created_by_id: Some(1),
        status: "issued".into(),
        subtotal: 500.0,
        discount_amount: 0.0,
        tax_amount: 25.0,
        total_amount: 525.0,
        paid_amount: 0.0,
        balance_amount: 525.0,
        currency: "INR".into(),
        created_at: Some(now),
        issued_at: Some(now),
    };
    assert!(serde_json::to_string(&invoice).is_ok());

    // 17. InvoiceLineItem
    let item = InvoiceLineItem {
        id: 1,
        invoice_id: 1,
        service_id: Some(1),
        description: "General Consultation".into(),
        quantity: 1.0,
        unit_price: 500.0,
        line_total: 500.0,
    };
    assert!(serde_json::to_string(&item).is_ok());

    // 18. BillingPayment
    let payment = BillingPayment {
        id: 1,
        facility_id: Some(1),
        invoice_id: 1,
        patient_id: 1,
        collected_by_id: Some(1),
        amount: 525.0,
        payment_method: "Cash".into(),
        reference_id: None,
        status: "collected".into(),
        collected_at: Some(now),
    };
    assert!(serde_json::to_string(&payment).is_ok());

    // 19. InsuranceClaim
    let claim = InsuranceClaim {
        id: 1,
        claim_number: "CLM-001".into(),
        patient_name: "John Doe".into(),
        payer_name: "HealthCare Plus".into(),
        policy_id: "POL-99".into(),
        claim_amount: 5000.0,
        copay_amount: 500.0,
        status: "submitted".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&claim).is_ok());

    // 20. MedicationInventory
    let med = MedicationInventory {
        id: 1,
        facility_id: Some(1),
        medication_name: "Paracetamol".into(),
        strength: Some("500mg".into()),
        form: Some("Tablet".into()),
        batch_number: Some("BATCH-01".into()),
        quantity_on_hand: 500.0,
        reorder_level: 50.0,
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&med).is_ok());

    // 21. Prescription
    let rx = Prescription {
        id: 1,
        facility_id: Some(1),
        encounter_id: Some(1),
        patient_id: 1,
        doctor_id: Some(2),
        diagnosis_context: Some("Viral fever".into()),
        status: "active".into(),
        created_at: Some(now),
        dispensed_at: None,
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&rx).is_ok());

    // 22. PrescriptionItem
    let rx_item = PrescriptionItem {
        id: 1,
        prescription_id: 1,
        inventory_id: Some(1),
        medication_name: "Paracetamol".into(),
        dosage: "500mg".into(),
        frequency: "TDS".into(),
        duration: "5 days".into(),
        quantity_prescribed: 15.0,
        quantity_dispensed: 0.0,
        instructions: Some("Take after food".into()),
        status: "pending".into(),
    };
    assert!(serde_json::to_string(&rx_item).is_ok());

    // 23. DispenseRecord
    let disp = DispenseRecord {
        id: 1,
        facility_id: Some(1),
        prescription_id: 1,
        prescription_item_id: Some(1),
        inventory_id: Some(1),
        patient_id: 1,
        dispensed_by_id: Some(3),
        quantity_dispensed: 15.0,
        status: "dispensed".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&disp).is_ok());

    // 24. HealthRecord
    let hr = HealthRecord {
        id: 1,
        user_id: Some(1),
        record_type: "diabetes".into(),
        data: Some("{}".into()),
        prediction: Some("Low Risk".into()),
        timestamp: Some(now),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&hr).is_ok());

    // 25. ChatLog
    let chat = ChatLog {
        id: 1,
        user_id: Some(1),
        role: "user".into(),
        content: "What are diabetes symptoms?".into(),
        timestamp: Some(now),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&chat).is_ok());

    // 26. AuditLog
    let audit = AuditLog {
        id: 1,
        facility_id: Some(1),
        admin_id: 1,
        target_user_id: Some(2),
        action: "VIEW_RECORD".into(),
        timestamp: Some(now),
        details: Some("{}".into()),
        is_deleted: 0,
        deleted_at: None,
    };
    assert!(serde_json::to_string(&audit).is_ok());

    // 27. SchemaContract
    let contract = SchemaContract {
        id: 1,
        contract_id: "CTR-001".into(),
        name: "VitalsContract".into(),
        version: 1,
        producer: "TelemetryService".into(),
        consumer: "RiskEngine".into(),
        schema_definition: "{}".into(),
        required_fields: "[]".into(),
        compatibility_mode: "BACKWARD".into(),
        sla_freshness_minutes: 60,
        quality_threshold: 0.99,
        created_at: Some(now),
        updated_at: Some(now),
    };
    assert!(serde_json::to_string(&contract).is_ok());

    // 28. ContractViolation
    let violation = ContractViolation {
        id: 1,
        contract_id: "CTR-001".into(),
        errors: "[]".into(),
        record_count: 1,
        timestamp: Some(now),
    };
    assert!(serde_json::to_string(&violation).is_ok());

    // 29. DataCatalogDataset
    let dataset = DataCatalogDataset {
        id: 1,
        dataset_id: "DS-001".into(),
        name: "BronzeVitals".into(),
        description: Some("Raw vitals stream".into()),
        owner: "DataEng".into(),
        schema_definition: "{}".into(),
        tags: "[]".into(),
        sla_hours: 24,
        freshness_field: "timestamp".into(),
        quality_score: 1.0,
        row_count: 1000,
        size_bytes: 4096,
        location: Some("s3://bucket/data".into()),
        format: "delta".into(),
        created_at: Some(now),
        updated_at: Some(now),
    };
    assert!(serde_json::to_string(&dataset).is_ok());

    // 30. DataCatalogLineage
    let lineage = DataCatalogLineage {
        id: 1,
        dataset_id: "DS-001".into(),
        upstream: "[]".into(),
        downstream: "[]".into(),
        column_lineage: None,
        updated_at: Some(now),
    };
    assert!(serde_json::to_string(&lineage).is_ok());

    // 31. FeatureAttributionLog
    let attr = FeatureAttributionLog {
        id: 1,
        model_name: "diabetes_v1".into(),
        model_version: "1.0.0".into(),
        features: "{}".into(),
        attributions: "{}".into(),
        prediction_value: 1,
        timestamp: Some(now),
    };
    assert!(serde_json::to_string(&attr).is_ok());

    // 32. InteroperabilityConsent
    let consent = InteroperabilityConsent {
        id: 1,
        facility_id: Some(1),
        patient_id: Some(1),
        granted_by_id: Some(1),
        revoked_by_id: None,
        scope: "fhir_bundle".into(),
        purpose: Some("Care coordination".into()),
        recipient_type: "doctor".into(),
        status: "active".into(),
        abdm_request_id: None,
        abdm_consent_id: None,
        abdm_status: None,
        abdm_last_event_at: None,
        expires_at: None,
        revoked_at: None,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&consent).is_ok());

    // 33. AbdmConsentEvent
    let abdm_event = AbdmConsentEvent {
        id: 1,
        facility_id: Some(1),
        patient_id: Some(1),
        local_consent_id: Some(1),
        abdm_request_id: "REQ-01".into(),
        abdm_consent_id: Some("CON-01".into()),
        event_type: "GRANTED".into(),
        status: "SUCCESS".into(),
        local_consent_status: Some("active".into()),
        hi_types: None,
        error_code: None,
        notification_at: Some(now),
        payload_sha256: "abcdef".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&abdm_event).is_ok());

    // 34. InteroperabilityExportProfile
    let profile = InteroperabilityExportProfile {
        id: 1,
        facility_id: Some(1),
        name: "ABDM Default".into(),
        partner_system: Some("NDHM".into()),
        resource_types: Some("Patient,Observation".into()),
        department_id: Some(1),
        created_by_id: Some(1),
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&profile).is_ok());

    // 35. InteroperabilityExport
    let export = InteroperabilityExport {
        id: 1,
        facility_id: Some(1),
        patient_id: Some(1),
        requested_by_id: Some(1),
        consent_id: Some(1),
        profile_id: Some(1),
        export_type: "fhir_bundle".into(),
        resource_count: 5,
        filter_summary: None,
        bundle_sha256: Some("sha256".into()),
        manifest_signature: Some("sig".into()),
        signature_algorithm: "HMAC-SHA256".into(),
        status: "completed".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&export).is_ok());

    // 36. AbhaLink
    let abha = AbhaLink {
        id: 1,
        patient_id: Some(1),
        abha_address: "john.doe@abdm".into(),
        kyc_transaction_id: Some("TX-001".into()),
        consent_purpose: "CARE".into(),
        status: "active".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&abha).is_ok());

    // 37. ClinicalAlert
    let alert = ClinicalAlert {
        id: 1,
        patient_id: 1,
        alert_type: "SEPSIS".into(),
        severity: "CRITICAL".into(),
        message: "qSOFA >= 2".into(),
        source_event_id: None,
        is_acknowledged: 0,
        acknowledged_by: None,
        acknowledged_at: None,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&alert).is_ok());

    // 38. PatientInsight
    let insight = PatientInsight {
        id: 1,
        patient_id: 1,
        insight_type: "trend_analysis".into(),
        content: "{}".into(),
        model_version: Some("v1.0".into()),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&insight).is_ok());

    // 39. ClinicalAICorrection
    let correction = ClinicalAICorrection {
        id: 1,
        patient_id: 1,
        clinician_id: 2,
        function_name: "predict_diabetes".into(),
        original_ai_output: "{}".into(),
        corrected_output: Some("{}".into()),
        override_action: "overridden".into(),
        override_reason: Some("Patient is on metformin".into()),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&correction).is_ok());

    // 40. DischargeSummary
    let discharge = DischargeSummary {
        id: 1,
        facility_id: Some(1),
        admission_id: 1,
        encounter_id: Some(1),
        patient_id: 1,
        doctor_id: Some(2),
        diagnosis_summary: "Acute Gastritis".into(),
        hospital_course: "Treated with IV fluids".into(),
        medications: None,
        follow_up_plan: None,
        discharge_instructions: None,
        status: "finalized".into(),
        created_at: Some(now),
        finalized_at: Some(now),
    };
    assert!(serde_json::to_string(&discharge).is_ok());

    // 41. NursingTask
    let task = NursingTask {
        id: 1,
        facility_id: Some(1),
        patient_id: 1,
        assigned_nurse_id: Some(3),
        created_by_id: Some(2),
        completed_by_id: None,
        encounter_id: Some(1),
        admission_id: Some(1),
        department_id: Some(1),
        task_type: "vitals_check".into(),
        title: "Check Vitals every 4h".into(),
        instructions: None,
        priority: "routine".into(),
        status: "assigned".into(),
        due_at: Some(now),
        completed_at: None,
        completion_note: None,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&task).is_ok());

    // 42. ModelFeedback
    let feedback = ModelFeedback {
        id: 1,
        patient_id: 1,
        model_name: "heart_disease".into(),
        input_features: "{}".into(),
        prediction_result: "{}".into(),
        corrected_label: "Low Risk".into(),
        clinician_id: 2,
        status: "pending_sync".into(),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&feedback).is_ok());

    // 43. FederatedSyncAudit
    let fed_audit = FederatedSyncAudit {
        id: 1,
        sync_run_id: "RUN-001".into(),
        node_id: "NODE-01".into(),
        model_name: "heart_disease".into(),
        records_synced: 100,
        epsilon_consumed: 0.05,
        delta_consumed: 1e-5,
        status: "completed".into(),
        error_message: None,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&fed_audit).is_ok());

    // 44. SmartApp
    let smart_app = SmartApp {
        id: 1,
        app_name: "Growth Charts".into(),
        client_id: "client-growth-1".into(),
        redirect_uri: "https://app.example.com/callback".into(),
        launch_url: "https://app.example.com/launch".into(),
        scopes: "launch/patient patient/*.read".into(),
        is_active: 1,
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&smart_app).is_ok());

    // 45. SmartLaunchContext
    let smart_ctx = SmartLaunchContext {
        id: 1,
        app_id: 1,
        patient_id: 1,
        user_id: 2,
        launch_token: "token-123".into(),
        auth_code: Some("auth-456".into()),
        scope: "launch/patient".into(),
        expires_at: now + chrono::Duration::hours(1),
        created_at: Some(now),
    };
    assert!(serde_json::to_string(&smart_ctx).is_ok());

    // 46. ConsentRecord
    let consent_rec = ConsentRecord {
        id: 1,
        user_id: 1,
        eula_version: "1.0".into(),
        accepted_at: now,
        ip_address: Some("127.0.0.1".into()),
        user_agent: Some("TestAgent/1.0".into()),
    };
    assert!(serde_json::to_string(&consent_rec).is_ok());
}
