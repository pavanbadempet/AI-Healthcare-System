use crate::db::DbPool;
use sqlx::Error;

/// SQL DDL Schema for SQLite
pub const SQLITE_SCHEMA: &str = r#"
-- 1. Hospital Facilities
CREATE TABLE IF NOT EXISTS hospital_facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    facility_type TEXT DEFAULT 'hospital',
    country TEXT,
    region TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_facilities_name ON hospital_facilities(name);

-- 2. Departments
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    name TEXT UNIQUE NOT NULL,
    department_type TEXT NOT NULL,
    location TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_departments_facility ON departments(facility_id);

-- 3. Users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    role TEXT DEFAULT 'patient' CHECK (role IN ('patient', 'doctor', 'nurse', 'pharmacist', 'billing', 'admin')),
    email TEXT UNIQUE,
    full_name TEXT,
    gender TEXT,
    blood_type TEXT,
    dob TEXT,
    height REAL,
    weight REAL,
    existing_ailments TEXT,
    profile_picture TEXT,
    about_me TEXT,
    diet TEXT,
    activity_level TEXT,
    sleep_hours REAL,
    stress_level TEXT,
    allow_data_collection INTEGER DEFAULT 1,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    plan_tier TEXT DEFAULT 'free',
    subscription_expiry DATETIME,
    razorpay_customer_id TEXT,
    consultation_fee REAL DEFAULT 500.0,
    specialization TEXT,
    psych_profile TEXT,
    totp_secret TEXT,
    is_totp_enabled INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_facility ON users(facility_id);
CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(is_deleted);

-- 4. Beds
CREATE TABLE IF NOT EXISTS beds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),
    bed_number TEXT NOT NULL,
    ward TEXT,
    status TEXT DEFAULT 'available',
    current_patient_id INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_beds_number ON beds(bed_number);
CREATE INDEX IF NOT EXISTS idx_beds_status ON beds(status);
CREATE INDEX IF NOT EXISTS idx_beds_patient ON beds(current_patient_id);

-- 5. Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    specialist TEXT,
    date_time DATETIME,
    reason TEXT,
    status TEXT DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_appointments_user_dt ON appointments(user_id, date_time);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);

-- 6. Encounters
CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    encounter_type TEXT NOT NULL,
    reason TEXT,
    priority TEXT DEFAULT 'routine',
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_encounters_patient_started ON encounters(patient_id, started_at);
CREATE INDEX IF NOT EXISTS idx_encounters_status ON encounters(status);

-- 7. Admissions
CREATE TABLE IF NOT EXISTS admissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    encounter_id INTEGER NOT NULL REFERENCES encounters(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    bed_id INTEGER REFERENCES beds(id),
    admitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    discharged_at DATETIME,
    reason TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'discharged', 'cancelled')),
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_admissions_patient_admitted ON admissions(patient_id, admitted_at);
CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions(status);

-- 8. DICOM Studies
CREATE TABLE IF NOT EXISTS dicom_studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_uid TEXT UNIQUE NOT NULL,
    patient_id INTEGER REFERENCES users(id),
    modality TEXT DEFAULT 'CT',
    target_vault TEXT DEFAULT 'PACS-PRIMARY-01',
    file_name TEXT NOT NULL,
    file_size_kb INTEGER DEFAULT 0,
    is_preamble_valid TEXT DEFAULT 'true',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dicom_study_uid ON dicom_studies(study_uid);

-- 9. Clinical Orders
CREATE TABLE IF NOT EXISTS clinical_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    encounter_id INTEGER REFERENCES encounters(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    order_type TEXT NOT NULL,
    title TEXT NOT NULL,
    priority TEXT DEFAULT 'routine',
    status TEXT DEFAULT 'ordered',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_clinical_orders_patient ON clinical_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_orders_doctor ON clinical_orders(doctor_id);

-- 10. Care Events
CREATE TABLE IF NOT EXISTS care_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    actor_user_id INTEGER REFERENCES users(id),
    encounter_id INTEGER REFERENCES encounters(id),
    department_id INTEGER REFERENCES departments(id),
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    severity TEXT DEFAULT 'info',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_care_events_patient ON care_events(patient_id);

-- 11. Vital Observations
CREATE TABLE IF NOT EXISTS vital_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    recorded_by_id INTEGER REFERENCES users(id),
    encounter_id INTEGER REFERENCES encounters(id),
    department_id INTEGER REFERENCES departments(id),
    source TEXT DEFAULT 'manual',
    heart_rate REAL,
    systolic_bp REAL,
    diastolic_bp REAL,
    spo2 REAL,
    temperature_c REAL,
    respiratory_rate REAL,
    blood_glucose REAL,
    observed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME,
    CONSTRAINT uq_vital_obs_patient_observed UNIQUE (patient_id, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_vital_obs_patient_observed ON vital_observations(patient_id, observed_at);

-- 12. Monitoring Signals
CREATE TABLE IF NOT EXISTS monitoring_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    vital_observation_id INTEGER REFERENCES vital_observations(id),
    encounter_id INTEGER REFERENCES encounters(id),
    department_id INTEGER REFERENCES departments(id),
    signal_type TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_monitoring_signal_vital_type UNIQUE (vital_observation_id, signal_type)
);
CREATE INDEX IF NOT EXISTS idx_monitoring_signals_status ON monitoring_signals(status);

-- 13. Diagnostic Results
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    order_id INTEGER NOT NULL REFERENCES clinical_orders(id),
    encounter_id INTEGER REFERENCES encounters(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    result_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    abnormal_flag INTEGER DEFAULT 0,
    status TEXT DEFAULT 'final',
    review_status TEXT DEFAULT 'pending_review',
    review_note TEXT,
    reviewed_by_id INTEGER REFERENCES users(id),
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_diagnostic_res_patient_created ON diagnostic_results(patient_id, created_at);

-- 14. Spark Streaming Metrics
CREATE TABLE IF NOT EXISTS spark_streaming_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    records_processed INTEGER NOT NULL,
    processing_time_ms REAL NOT NULL,
    ml_latency_ms REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 15. Billable Services
CREATE TABLE IF NOT EXISTS billable_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    service_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    service_type TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    unit_price REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_billable_services_code ON billable_services(service_code);

-- 16. Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    encounter_id INTEGER REFERENCES encounters(id),
    admission_id INTEGER REFERENCES admissions(id),
    created_by_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'issued',
    subtotal REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    tax_amount REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    paid_amount REAL DEFAULT 0,
    balance_amount REAL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_invoices_patient ON invoices(patient_id);

-- 17. Invoice Line Items
CREATE TABLE IF NOT EXISTS invoice_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES billable_services(id),
    description TEXT NOT NULL,
    quantity REAL DEFAULT 1,
    unit_price REAL DEFAULT 0,
    line_total REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_line_items(invoice_id);

-- 18. Billing Payments
CREATE TABLE IF NOT EXISTS billing_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    collected_by_id INTEGER REFERENCES users(id),
    amount REAL DEFAULT 0,
    payment_method TEXT NOT NULL,
    reference_id TEXT,
    status TEXT DEFAULT 'collected',
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_billing_payments_invoice ON billing_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_billing_payments_patient ON billing_payments(patient_id);

-- 19. Insurance Claims
CREATE TABLE IF NOT EXISTS insurance_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_number TEXT UNIQUE NOT NULL,
    patient_name TEXT NOT NULL,
    payer_name TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    claim_amount REAL DEFAULT 0,
    copay_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'submitted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_insurance_claims_number ON insurance_claims(claim_number);

-- 20. Medication Inventory
CREATE TABLE IF NOT EXISTS medication_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    medication_name TEXT NOT NULL,
    strength TEXT,
    form TEXT,
    batch_number TEXT,
    quantity_on_hand REAL DEFAULT 0,
    reorder_level REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_med_inv_name ON medication_inventory(medication_name);
CREATE INDEX IF NOT EXISTS idx_med_inv_batch ON medication_inventory(batch_number);

-- 21. Prescriptions
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    encounter_id INTEGER REFERENCES encounters(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    diagnosis_context TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dispensed_at DATETIME,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient_created ON prescriptions(patient_id, created_at);

-- 22. Prescription Items
CREATE TABLE IF NOT EXISTS prescription_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    inventory_id INTEGER REFERENCES medication_inventory(id),
    medication_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    duration TEXT NOT NULL,
    quantity_prescribed REAL DEFAULT 1,
    quantity_dispensed REAL DEFAULT 0,
    instructions TEXT,
    status TEXT DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_prescription_items_prescription ON prescription_items(prescription_id);

-- 23. Dispense Records
CREATE TABLE IF NOT EXISTS dispense_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id),
    prescription_item_id INTEGER REFERENCES prescription_items(id),
    inventory_id INTEGER REFERENCES medication_inventory(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    dispensed_by_id INTEGER REFERENCES users(id),
    quantity_dispensed REAL DEFAULT 0,
    status TEXT DEFAULT 'dispensed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dispense_records_prescription ON dispense_records(prescription_id);

-- 24. Health Records
CREATE TABLE IF NOT EXISTS health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    record_type TEXT NOT NULL CHECK (record_type IN ('diabetes', 'heart', 'liver', 'kidney', 'lungs')),
    data TEXT,
    prediction TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_health_records_user_timestamp ON health_records(user_id, timestamp);

-- 25. Chat Logs
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id);

-- 26. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    admin_id INTEGER NOT NULL REFERENCES users(id),
    target_user_id INTEGER,
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_timestamp ON audit_logs(admin_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_timestamp ON audit_logs(target_user_id, timestamp);

-- 27. Schema Contracts
CREATE TABLE IF NOT EXISTS schema_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    producer TEXT NOT NULL,
    consumer TEXT NOT NULL,
    schema_definition TEXT NOT NULL,
    required_fields TEXT NOT NULL,
    compatibility_mode TEXT DEFAULT 'BACKWARD' NOT NULL,
    sla_freshness_minutes INTEGER DEFAULT 1440 NOT NULL,
    quality_threshold REAL DEFAULT 0.95 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_schema_contracts_cid ON schema_contracts(contract_id);

-- 28. Contract Violations
CREATE TABLE IF NOT EXISTS contract_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL REFERENCES schema_contracts(contract_id) ON DELETE CASCADE,
    errors TEXT NOT NULL,
    record_count INTEGER DEFAULT 1 NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_contract_violations_cid ON contract_violations(contract_id);

-- 29. Data Catalog Datasets
CREATE TABLE IF NOT EXISTS data_catalog_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT NOT NULL,
    schema_definition TEXT NOT NULL,
    tags TEXT NOT NULL,
    sla_hours INTEGER DEFAULT 24 NOT NULL,
    freshness_field TEXT DEFAULT 'timestamp' NOT NULL,
    quality_score REAL DEFAULT 1.0 NOT NULL,
    row_count INTEGER DEFAULT 0 NOT NULL,
    size_bytes INTEGER DEFAULT 0 NOT NULL,
    location TEXT,
    format TEXT DEFAULT 'json' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_data_catalog_dataset_id ON data_catalog_datasets(dataset_id);

-- 30. Data Catalog Lineage
CREATE TABLE IF NOT EXISTS data_catalog_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL REFERENCES data_catalog_datasets(dataset_id) ON DELETE CASCADE,
    upstream TEXT NOT NULL,
    downstream TEXT NOT NULL,
    column_lineage TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_data_catalog_lineage_did ON data_catalog_lineage(dataset_id);

-- 31. Feature Attribution Logs
CREATE TABLE IF NOT EXISTS feature_attribution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    features TEXT NOT NULL,
    attributions TEXT NOT NULL,
    prediction_value INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feature_attr_model ON feature_attribution_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_feature_attr_timestamp ON feature_attribution_logs(timestamp);

-- 32. Interoperability Consents
CREATE TABLE IF NOT EXISTS interoperability_consents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER REFERENCES users(id),
    granted_by_id INTEGER REFERENCES users(id),
    revoked_by_id INTEGER REFERENCES users(id),
    scope TEXT DEFAULT 'fhir_bundle_export',
    purpose TEXT,
    recipient_type TEXT DEFAULT 'care_team',
    status TEXT DEFAULT 'active',
    abdm_request_id TEXT,
    abdm_consent_id TEXT,
    abdm_status TEXT,
    abdm_last_event_at DATETIME,
    expires_at DATETIME,
    revoked_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_interop_consents_patient ON interoperability_consents(patient_id);
CREATE INDEX IF NOT EXISTS idx_interop_consents_abdm_req ON interoperability_consents(abdm_request_id);

-- 33. ABDM Consent Events
CREATE TABLE IF NOT EXISTS abdm_consent_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER REFERENCES users(id),
    local_consent_id INTEGER REFERENCES interoperability_consents(id),
    abdm_request_id TEXT NOT NULL,
    abdm_consent_id TEXT,
    event_type TEXT DEFAULT 'consent_status',
    status TEXT NOT NULL,
    local_consent_status TEXT,
    hi_types TEXT,
    error_code TEXT,
    notification_at DATETIME,
    payload_sha256 TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_abdm_events_req_id ON abdm_consent_events(abdm_request_id);

-- 34. Interoperability Export Profiles
CREATE TABLE IF NOT EXISTS interoperability_export_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    name TEXT NOT NULL,
    partner_system TEXT,
    resource_types TEXT,
    department_id INTEGER REFERENCES departments(id),
    created_by_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_interop_profiles_name ON interoperability_export_profiles(name);

-- 35. Interoperability Exports
CREATE TABLE IF NOT EXISTS interoperability_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    requested_by_id INTEGER REFERENCES users(id),
    consent_id INTEGER REFERENCES interoperability_consents(id),
    profile_id INTEGER REFERENCES interoperability_export_profiles(id),
    export_type TEXT DEFAULT 'fhir_bundle',
    resource_count INTEGER DEFAULT 0,
    filter_summary TEXT,
    bundle_sha256 TEXT,
    manifest_signature TEXT,
    signature_algorithm TEXT DEFAULT 'HMAC-SHA256',
    status TEXT DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_interop_exports_patient ON interoperability_exports(patient_id);

-- 36. ABHA Links
CREATE TABLE IF NOT EXISTS abha_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER REFERENCES users(id),
    abha_address TEXT UNIQUE NOT NULL,
    kyc_transaction_id TEXT,
    consent_purpose TEXT DEFAULT 'CARE_MANAGEMENT',
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_abha_links_address ON abha_links(abha_address);

-- 37. Clinical Alerts
CREATE TABLE IF NOT EXISTS clinical_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES users(id),
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    source_event_id TEXT,
    is_acknowledged INTEGER DEFAULT 0,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clinical_alerts_patient ON clinical_alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_alerts_type ON clinical_alerts(alert_type);

-- 38. Patient Insights
CREATE TABLE IF NOT EXISTS patient_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES users(id),
    insight_type TEXT NOT NULL,
    content TEXT NOT NULL,
    model_version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_patient_insights_patient ON patient_insights(patient_id);

-- 39. Clinical AI Corrections
CREATE TABLE IF NOT EXISTS clinical_ai_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES users(id),
    clinician_id INTEGER NOT NULL REFERENCES users(id),
    function_name TEXT NOT NULL,
    original_ai_output TEXT NOT NULL,
    corrected_output TEXT,
    override_action TEXT NOT NULL,
    override_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_corrections_patient ON clinical_ai_corrections(patient_id);
CREATE INDEX IF NOT EXISTS idx_ai_corrections_function ON clinical_ai_corrections(function_name);

-- 40. Discharge Summaries
CREATE TABLE IF NOT EXISTS discharge_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    admission_id INTEGER NOT NULL REFERENCES admissions(id),
    encounter_id INTEGER REFERENCES encounters(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER REFERENCES users(id),
    diagnosis_summary TEXT NOT NULL,
    hospital_course TEXT NOT NULL,
    medications TEXT,
    follow_up_plan TEXT,
    discharge_instructions TEXT,
    status TEXT DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finalized_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_discharge_summaries_admission ON discharge_summaries(admission_id);

-- 41. Nursing Tasks
CREATE TABLE IF NOT EXISTS nursing_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER REFERENCES hospital_facilities(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    assigned_nurse_id INTEGER REFERENCES users(id),
    created_by_id INTEGER REFERENCES users(id),
    completed_by_id INTEGER REFERENCES users(id),
    encounter_id INTEGER REFERENCES encounters(id),
    admission_id INTEGER REFERENCES admissions(id),
    department_id INTEGER REFERENCES departments(id),
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    instructions TEXT,
    priority TEXT DEFAULT 'routine',
    status TEXT DEFAULT 'assigned',
    due_at DATETIME,
    completed_at DATETIME,
    completion_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nursing_tasks_patient ON nursing_tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_nursing_tasks_nurse ON nursing_tasks(assigned_nurse_id);

-- 42. Model Feedbacks
CREATE TABLE IF NOT EXISTS model_feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES users(id),
    model_name TEXT NOT NULL,
    input_features TEXT NOT NULL,
    prediction_result TEXT NOT NULL,
    corrected_label TEXT NOT NULL,
    clinician_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT DEFAULT 'pending_sync',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_model_feedbacks_patient ON model_feedbacks(patient_id);
CREATE INDEX IF NOT EXISTS idx_model_feedbacks_model ON model_feedbacks(model_name);

-- 43. Federated Sync Audits
CREATE TABLE IF NOT EXISTS federated_sync_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_run_id TEXT UNIQUE NOT NULL,
    node_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    records_synced INTEGER DEFAULT 0 NOT NULL,
    epsilon_consumed REAL DEFAULT 0.0 NOT NULL,
    delta_consumed REAL DEFAULT 0.0 NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fed_sync_run_id ON federated_sync_audits(sync_run_id);

-- 44. SMART Apps
CREATE TABLE IF NOT EXISTS smart_apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT UNIQUE NOT NULL,
    client_id TEXT UNIQUE NOT NULL,
    redirect_uri TEXT NOT NULL,
    launch_url TEXT NOT NULL,
    scopes TEXT DEFAULT 'launch/patient patient/*.read',
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smart_apps_client_id ON smart_apps(client_id);

-- 45. SMART Launch Contexts
CREATE TABLE IF NOT EXISTS smart_launch_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL REFERENCES smart_apps(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    launch_token TEXT UNIQUE NOT NULL,
    auth_code TEXT,
    scope TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smart_launch_token ON smart_launch_contexts(launch_token);

-- 46. Consent Records (EULA)
CREATE TABLE IF NOT EXISTS consent_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    eula_version TEXT NOT NULL,
    accepted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);
CREATE INDEX IF NOT EXISTS idx_consent_records_user ON consent_records(user_id);
"#;

/// SQL DDL Schema for PostgreSQL
pub const POSTGRES_SCHEMA: &str = r#"
-- 1. Hospital Facilities
CREATE TABLE IF NOT EXISTS hospital_facilities (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    facility_type VARCHAR(64) DEFAULT 'hospital',
    country VARCHAR(128),
    region VARCHAR(128),
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Departments
CREATE TABLE IF NOT EXISTS departments (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    name VARCHAR(255) UNIQUE NOT NULL,
    department_type VARCHAR(64) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Users
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(64) DEFAULT 'patient' CHECK (role IN ('patient', 'doctor', 'nurse', 'pharmacist', 'billing', 'admin')),
    email TEXT UNIQUE,
    full_name TEXT,
    gender TEXT,
    blood_type TEXT,
    dob TEXT,
    height DOUBLE PRECISION,
    weight DOUBLE PRECISION,
    existing_ailments TEXT,
    profile_picture TEXT,
    about_me TEXT,
    diet VARCHAR(64),
    activity_level VARCHAR(64),
    sleep_hours DOUBLE PRECISION,
    stress_level VARCHAR(64),
    allow_data_collection BIGINT DEFAULT 1,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    plan_tier VARCHAR(64) DEFAULT 'free',
    subscription_expiry TIMESTAMPTZ,
    razorpay_customer_id VARCHAR(255),
    consultation_fee DOUBLE PRECISION DEFAULT 500.0,
    specialization VARCHAR(255),
    psych_profile TEXT,
    totp_secret TEXT,
    is_totp_enabled BIGINT DEFAULT 0,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 4. Beds
CREATE TABLE IF NOT EXISTS beds (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    department_id BIGINT NOT NULL REFERENCES departments(id),
    bed_number VARCHAR(64) NOT NULL,
    ward VARCHAR(128),
    status VARCHAR(64) DEFAULT 'available',
    current_patient_id BIGINT REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    specialist VARCHAR(255),
    date_time TIMESTAMPTZ,
    reason TEXT,
    status VARCHAR(64) DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 6. Encounters
CREATE TABLE IF NOT EXISTS encounters (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    department_id BIGINT REFERENCES departments(id),
    encounter_type VARCHAR(64) NOT NULL,
    reason TEXT,
    priority VARCHAR(64) DEFAULT 'routine',
    status VARCHAR(64) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 7. Admissions
CREATE TABLE IF NOT EXISTS admissions (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    encounter_id BIGINT NOT NULL REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    department_id BIGINT REFERENCES departments(id),
    bed_id BIGINT REFERENCES beds(id),
    admitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    discharged_at TIMESTAMPTZ,
    reason TEXT,
    status VARCHAR(64) DEFAULT 'active' CHECK (status IN ('active', 'discharged', 'cancelled')),
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 8. DICOM Studies
CREATE TABLE IF NOT EXISTS dicom_studies (
    id BIGSERIAL PRIMARY KEY,
    study_uid VARCHAR(255) UNIQUE NOT NULL,
    patient_id BIGINT REFERENCES users(id),
    modality VARCHAR(64) DEFAULT 'CT',
    target_vault VARCHAR(128) DEFAULT 'PACS-PRIMARY-01',
    file_name VARCHAR(255) NOT NULL,
    file_size_kb BIGINT DEFAULT 0,
    is_preamble_valid VARCHAR(64) DEFAULT 'true',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 9. Clinical Orders
CREATE TABLE IF NOT EXISTS clinical_orders (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    encounter_id BIGINT REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    department_id BIGINT REFERENCES departments(id),
    order_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    priority VARCHAR(64) DEFAULT 'routine',
    status VARCHAR(64) DEFAULT 'ordered',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- 10. Care Events
CREATE TABLE IF NOT EXISTS care_events (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    actor_user_id BIGINT REFERENCES users(id),
    encounter_id BIGINT REFERENCES encounters(id),
    department_id BIGINT REFERENCES departments(id),
    event_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    severity VARCHAR(64) DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. Vital Observations
CREATE TABLE IF NOT EXISTS vital_observations (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    recorded_by_id BIGINT REFERENCES users(id),
    encounter_id BIGINT REFERENCES encounters(id),
    department_id BIGINT REFERENCES departments(id),
    source VARCHAR(64) DEFAULT 'manual',
    heart_rate DOUBLE PRECISION,
    systolic_bp DOUBLE PRECISION,
    diastolic_bp DOUBLE PRECISION,
    spo2 DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION,
    respiratory_rate DOUBLE PRECISION,
    blood_glucose DOUBLE PRECISION,
    observed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_vital_obs_patient_observed UNIQUE (patient_id, observed_at)
);

-- 12. Monitoring Signals
CREATE TABLE IF NOT EXISTS monitoring_signals (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    vital_observation_id BIGINT REFERENCES vital_observations(id),
    encounter_id BIGINT REFERENCES encounters(id),
    department_id BIGINT REFERENCES departments(id),
    signal_type VARCHAR(64) NOT NULL,
    severity VARCHAR(64) DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    status VARCHAR(64) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_monitoring_signal_vital_type UNIQUE (vital_observation_id, signal_type)
);

-- 13. Diagnostic Results
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    order_id BIGINT NOT NULL REFERENCES clinical_orders(id),
    encounter_id BIGINT REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    department_id BIGINT REFERENCES departments(id),
    result_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    abnormal_flag BIGINT DEFAULT 0,
    status VARCHAR(64) DEFAULT 'final',
    review_status VARCHAR(64) DEFAULT 'pending_review',
    review_note TEXT,
    reviewed_by_id BIGINT REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 14. Spark Streaming Metrics
CREATE TABLE IF NOT EXISTS spark_streaming_metrics (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    records_processed BIGINT NOT NULL,
    processing_time_ms DOUBLE PRECISION NOT NULL,
    ml_latency_ms DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 15. Billable Services
CREATE TABLE IF NOT EXISTS billable_services (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    service_code VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(64) NOT NULL,
    department_id BIGINT REFERENCES departments(id),
    unit_price DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 16. Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    encounter_id BIGINT REFERENCES encounters(id),
    admission_id BIGINT REFERENCES admissions(id),
    created_by_id BIGINT REFERENCES users(id),
    status VARCHAR(64) DEFAULT 'issued',
    subtotal DOUBLE PRECISION DEFAULT 0,
    discount_amount DOUBLE PRECISION DEFAULT 0,
    tax_amount DOUBLE PRECISION DEFAULT 0,
    total_amount DOUBLE PRECISION DEFAULT 0,
    paid_amount DOUBLE PRECISION DEFAULT 0,
    balance_amount DOUBLE PRECISION DEFAULT 0,
    currency VARCHAR(16) DEFAULT 'INR',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    issued_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 17. Invoice Line Items
CREATE TABLE IF NOT EXISTS invoice_line_items (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    service_id BIGINT REFERENCES billable_services(id),
    description VARCHAR(255) NOT NULL,
    quantity DOUBLE PRECISION DEFAULT 1,
    unit_price DOUBLE PRECISION DEFAULT 0,
    line_total DOUBLE PRECISION DEFAULT 0
);

-- 18. Billing Payments
CREATE TABLE IF NOT EXISTS billing_payments (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    invoice_id BIGINT NOT NULL REFERENCES invoices(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    collected_by_id BIGINT REFERENCES users(id),
    amount DOUBLE PRECISION DEFAULT 0,
    payment_method VARCHAR(64) NOT NULL,
    reference_id VARCHAR(255),
    status VARCHAR(64) DEFAULT 'collected',
    collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 19. Insurance Claims
CREATE TABLE IF NOT EXISTS insurance_claims (
    id BIGSERIAL PRIMARY KEY,
    claim_number VARCHAR(128) UNIQUE NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    payer_name VARCHAR(255) NOT NULL,
    policy_id VARCHAR(128) NOT NULL,
    claim_amount DOUBLE PRECISION DEFAULT 0,
    copay_amount DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(64) DEFAULT 'submitted',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 20. Medication Inventory
CREATE TABLE IF NOT EXISTS medication_inventory (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    medication_name VARCHAR(255) NOT NULL,
    strength VARCHAR(64),
    form VARCHAR(64),
    batch_number VARCHAR(128),
    quantity_on_hand DOUBLE PRECISION DEFAULT 0,
    reorder_level DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 21. Prescriptions
CREATE TABLE IF NOT EXISTS prescriptions (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    encounter_id BIGINT REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    diagnosis_context TEXT,
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    dispensed_at TIMESTAMPTZ,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 22. Prescription Items
CREATE TABLE IF NOT EXISTS prescription_items (
    id BIGSERIAL PRIMARY KEY,
    prescription_id BIGINT NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    inventory_id BIGINT REFERENCES medication_inventory(id),
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(64) NOT NULL,
    frequency VARCHAR(64) NOT NULL,
    duration VARCHAR(64) NOT NULL,
    quantity_prescribed DOUBLE PRECISION DEFAULT 1,
    quantity_dispensed DOUBLE PRECISION DEFAULT 0,
    instructions TEXT,
    status VARCHAR(64) DEFAULT 'pending'
);

-- 23. Dispense Records
CREATE TABLE IF NOT EXISTS dispense_records (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    prescription_id BIGINT NOT NULL REFERENCES prescriptions(id),
    prescription_item_id BIGINT REFERENCES prescription_items(id),
    inventory_id BIGINT REFERENCES medication_inventory(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    dispensed_by_id BIGINT REFERENCES users(id),
    quantity_dispensed DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(64) DEFAULT 'dispensed',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 24. Health Records
CREATE TABLE IF NOT EXISTS health_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    record_type VARCHAR(64) NOT NULL CHECK (record_type IN ('diabetes', 'heart', 'liver', 'kidney', 'lungs')),
    data TEXT,
    prediction VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 25. Chat Logs
CREATE TABLE IF NOT EXISTS chat_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    role VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 26. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    admin_id BIGINT NOT NULL REFERENCES users(id),
    target_user_id BIGINT,
    action VARCHAR(128) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    is_deleted BIGINT DEFAULT 0,
    deleted_at TIMESTAMPTZ
);

-- 27. Schema Contracts
CREATE TABLE IF NOT EXISTS schema_contracts (
    id BIGSERIAL PRIMARY KEY,
    contract_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    version BIGINT DEFAULT 1 NOT NULL,
    producer VARCHAR(255) NOT NULL,
    consumer VARCHAR(255) NOT NULL,
    schema_definition JSONB NOT NULL,
    required_fields JSONB NOT NULL,
    compatibility_mode VARCHAR(64) DEFAULT 'BACKWARD' NOT NULL,
    sla_freshness_minutes BIGINT DEFAULT 1440 NOT NULL,
    quality_threshold DOUBLE PRECISION DEFAULT 0.95 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 28. Contract Violations
CREATE TABLE IF NOT EXISTS contract_violations (
    id BIGSERIAL PRIMARY KEY,
    contract_id VARCHAR(255) NOT NULL REFERENCES schema_contracts(contract_id) ON DELETE CASCADE,
    errors JSONB NOT NULL,
    record_count BIGINT DEFAULT 1 NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 29. Data Catalog Datasets
CREATE TABLE IF NOT EXISTS data_catalog_datasets (
    id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner VARCHAR(255) NOT NULL,
    schema_definition JSONB NOT NULL,
    tags JSONB NOT NULL,
    sla_hours BIGINT DEFAULT 24 NOT NULL,
    freshness_field VARCHAR(128) DEFAULT 'timestamp' NOT NULL,
    quality_score DOUBLE PRECISION DEFAULT 1.0 NOT NULL,
    row_count BIGINT DEFAULT 0 NOT NULL,
    size_bytes BIGINT DEFAULT 0 NOT NULL,
    location TEXT,
    format VARCHAR(64) DEFAULT 'json' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 30. Data Catalog Lineage
CREATE TABLE IF NOT EXISTS data_catalog_lineage (
    id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL REFERENCES data_catalog_datasets(dataset_id) ON DELETE CASCADE,
    upstream JSONB NOT NULL,
    downstream JSONB NOT NULL,
    column_lineage JSONB,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 31. Feature Attribution Logs
CREATE TABLE IF NOT EXISTS feature_attribution_logs (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(128) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    features JSONB NOT NULL,
    attributions JSONB NOT NULL,
    prediction_value BIGINT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 32. Interoperability Consents
CREATE TABLE IF NOT EXISTS interoperability_consents (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT REFERENCES users(id),
    granted_by_id BIGINT REFERENCES users(id),
    revoked_by_id BIGINT REFERENCES users(id),
    scope VARCHAR(128) DEFAULT 'fhir_bundle_export',
    purpose TEXT,
    recipient_type VARCHAR(64) DEFAULT 'care_team',
    status VARCHAR(64) DEFAULT 'active',
    abdm_request_id VARCHAR(255),
    abdm_consent_id VARCHAR(255),
    abdm_status VARCHAR(64),
    abdm_last_event_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 33. ABDM Consent Events
CREATE TABLE IF NOT EXISTS abdm_consent_events (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT REFERENCES users(id),
    local_consent_id BIGINT REFERENCES interoperability_consents(id),
    abdm_request_id VARCHAR(255) NOT NULL,
    abdm_consent_id VARCHAR(255),
    event_type VARCHAR(64) DEFAULT 'consent_status',
    status VARCHAR(64) NOT NULL,
    local_consent_status VARCHAR(64),
    hi_types TEXT,
    error_code VARCHAR(64),
    notification_at TIMESTAMPTZ,
    payload_sha256 VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 34. Interoperability Export Profiles
CREATE TABLE IF NOT EXISTS interoperability_export_profiles (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    name VARCHAR(255) NOT NULL,
    partner_system VARCHAR(255),
    resource_types TEXT,
    department_id BIGINT REFERENCES departments(id),
    created_by_id BIGINT REFERENCES users(id),
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 35. Interoperability Exports
CREATE TABLE IF NOT EXISTS interoperability_exports (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    requested_by_id BIGINT REFERENCES users(id),
    consent_id BIGINT REFERENCES interoperability_consents(id),
    profile_id BIGINT REFERENCES interoperability_export_profiles(id),
    export_type VARCHAR(64) DEFAULT 'fhir_bundle',
    resource_count BIGINT DEFAULT 0,
    filter_summary TEXT,
    bundle_sha256 VARCHAR(255),
    manifest_signature VARCHAR(255),
    signature_algorithm VARCHAR(64) DEFAULT 'HMAC-SHA256',
    status VARCHAR(64) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 36. ABHA Links
CREATE TABLE IF NOT EXISTS abha_links (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT REFERENCES users(id),
    abha_address VARCHAR(255) UNIQUE NOT NULL,
    kyc_transaction_id VARCHAR(255),
    consent_purpose VARCHAR(128) DEFAULT 'CARE_MANAGEMENT',
    status VARCHAR(64) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 37. Clinical Alerts
CREATE TABLE IF NOT EXISTS clinical_alerts (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES users(id),
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    source_event_id VARCHAR(255),
    is_acknowledged BIGINT DEFAULT 0,
    acknowledged_by BIGINT REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 38. Patient Insights
CREATE TABLE IF NOT EXISTS patient_insights (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES users(id),
    insight_type VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    model_version VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 39. Clinical AI Corrections
CREATE TABLE IF NOT EXISTS clinical_ai_corrections (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES users(id),
    clinician_id BIGINT NOT NULL REFERENCES users(id),
    function_name VARCHAR(128) NOT NULL,
    original_ai_output TEXT NOT NULL,
    corrected_output TEXT,
    override_action VARCHAR(64) NOT NULL,
    override_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 40. Discharge Summaries
CREATE TABLE IF NOT EXISTS discharge_summaries (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    admission_id BIGINT NOT NULL REFERENCES admissions(id),
    encounter_id BIGINT REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    doctor_id BIGINT REFERENCES users(id),
    diagnosis_summary TEXT NOT NULL,
    hospital_course TEXT NOT NULL,
    medications TEXT,
    follow_up_plan TEXT,
    discharge_instructions TEXT,
    status VARCHAR(64) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    finalized_at TIMESTAMPTZ
);

-- 41. Nursing Tasks
CREATE TABLE IF NOT EXISTS nursing_tasks (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES hospital_facilities(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    assigned_nurse_id BIGINT REFERENCES users(id),
    created_by_id BIGINT REFERENCES users(id),
    completed_by_id BIGINT REFERENCES users(id),
    encounter_id BIGINT REFERENCES encounters(id),
    admission_id BIGINT REFERENCES admissions(id),
    department_id BIGINT REFERENCES departments(id),
    task_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    instructions TEXT,
    priority VARCHAR(64) DEFAULT 'routine',
    status VARCHAR(64) DEFAULT 'assigned',
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    completion_note TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 42. Model Feedbacks
CREATE TABLE IF NOT EXISTS model_feedbacks (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES users(id),
    model_name VARCHAR(128) NOT NULL,
    input_features TEXT NOT NULL,
    prediction_result TEXT NOT NULL,
    corrected_label VARCHAR(128) NOT NULL,
    clinician_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(64) DEFAULT 'pending_sync',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 43. Federated Sync Audits
CREATE TABLE IF NOT EXISTS federated_sync_audits (
    id BIGSERIAL PRIMARY KEY,
    sync_run_id VARCHAR(255) UNIQUE NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    records_synced BIGINT DEFAULT 0 NOT NULL,
    epsilon_consumed DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    delta_consumed DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    status VARCHAR(64) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 44. SMART Apps
CREATE TABLE IF NOT EXISTS smart_apps (
    id BIGSERIAL PRIMARY KEY,
    app_name VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    redirect_uri VARCHAR(255) NOT NULL,
    launch_url VARCHAR(255) NOT NULL,
    scopes VARCHAR(255) DEFAULT 'launch/patient patient/*.read',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 45. SMART Launch Contexts
CREATE TABLE IF NOT EXISTS smart_launch_contexts (
    id BIGSERIAL PRIMARY KEY,
    app_id BIGINT NOT NULL REFERENCES smart_apps(id),
    patient_id BIGINT NOT NULL REFERENCES users(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    launch_token VARCHAR(255) UNIQUE NOT NULL,
    auth_code VARCHAR(255),
    scope VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 46. Consent Records (EULA)
CREATE TABLE IF NOT EXISTS consent_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    eula_version VARCHAR(64) NOT NULL,
    accepted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(128),
    user_agent VARCHAR(512)
);
"#;

/// Automatically initialize all 46 database tables and indexes on the connection pool
/// Automatically initialize all 46 database tables and indexes on the connection pool,
/// and seed default administrative and clinical records if absent.
pub async fn init_schema(pool: &DbPool) -> Result<(), Error> {
    match pool {
        DbPool::Sqlite(p) => {
            // Split by ';' and execute statement by statement, ignoring empty statements
            for raw_statement in SQLITE_SCHEMA.split(';') {
                let stmt = raw_statement.trim();
                if !stmt.is_empty() {
                    sqlx::query(stmt).execute(p).await?;
                }
            }
        }
        DbPool::Postgres(p) => {
            for raw_statement in POSTGRES_SCHEMA.split(';') {
                let stmt = raw_statement.trim();
                if !stmt.is_empty() {
                    let _ = sqlx::query(stmt).execute(p).await;
                }
            }

            // Ensure any legacy boolean is_deleted columns or int4 columns are migrated to BIGINT
            let migration_block = r#"
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT table_name 
                        FROM information_schema.columns 
                        WHERE column_name = 'is_deleted' 
                          AND data_type = 'boolean' 
                          AND table_schema = 'public'
                    ) LOOP
                        EXECUTE format('ALTER TABLE %I ALTER COLUMN is_deleted DROP DEFAULT', r.table_name);
                        EXECUTE format('ALTER TABLE %I ALTER COLUMN is_deleted TYPE BIGINT USING (CASE WHEN is_deleted THEN 1 ELSE 0 END)', r.table_name);
                        EXECUTE format('ALTER TABLE %I ALTER COLUMN is_deleted SET DEFAULT 0', r.table_name);
                    END LOOP;

                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'id' AND data_type = 'integer') THEN
                        ALTER TABLE users ALTER COLUMN id TYPE BIGINT;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_totp_enabled' AND data_type = 'integer') THEN
                        ALTER TABLE users ALTER COLUMN is_totp_enabled TYPE BIGINT;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'allow_data_collection' AND data_type = 'integer') THEN
                        ALTER TABLE users ALTER COLUMN allow_data_collection TYPE BIGINT;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'facility_id' AND data_type = 'integer') THEN
                        ALTER TABLE users ALTER COLUMN facility_id TYPE BIGINT;
                    END IF;
                END $$;
            "#;
            let _ = sqlx::query(migration_block).execute(p).await;
        }
    }

    // Seed default administrative and clinical records
    seed_defaults(pool).await?;

    Ok(())
}

async fn seed_defaults(pool: &DbPool) -> Result<(), Error> {
    // 1. Seed Hospital Facility #1
    let facility_sql = r#"
        INSERT INTO hospital_facilities (id, name, facility_type, country, region, status)
        VALUES (1, 'General Hospital', 'hospital', 'US', 'North', 'active')
        ON CONFLICT (id) DO NOTHING
    "#;
    match pool {
        DbPool::Sqlite(p) => { let _ = sqlx::query(facility_sql).execute(p).await; },
        DbPool::Postgres(p) => { let _ = sqlx::query(facility_sql).execute(p).await; },
    };

    // 2. Seed Departments
    let dept_sql = r#"
        INSERT INTO departments (id, facility_id, name, department_type, status)
        VALUES (1, 1, 'Cardiology', 'clinical', 'active')
        ON CONFLICT (id) DO NOTHING
    "#;
    match pool {
        DbPool::Sqlite(p) => { let _ = sqlx::query(dept_sql).execute(p).await; },
        DbPool::Postgres(p) => { let _ = sqlx::query(dept_sql).execute(p).await; },
    };

    // 3. Seed Default Users
    let admin_hash = bcrypt::hash("Admin123!", 4)
        .unwrap_or_else(|_| "$2b$12$e8kPqZq1yF0P7r5e0t7G/.XmF6xH.K8/J9O3x6k3R7Q8Z9J9O3x6k".to_string());
    let doctor_hash = bcrypt::hash("Doctor123!", 4).unwrap_or_else(|_| admin_hash.clone());
    let nurse_hash = bcrypt::hash("Nurse123!", 4).unwrap_or_else(|_| admin_hash.clone());
    let patient_hash = bcrypt::hash("Patient123!", 4).unwrap_or_else(|_| admin_hash.clone());

    let seed_users = [
        ("admin", &admin_hash, "admin", "admin@hospital.org", "System Administrator"),
        ("admin_e2e", &admin_hash, "admin", "admin_e2e@hospital.org", "E2E Admin"),
        ("doctor", &doctor_hash, "doctor", "doctor@hospital.org", "Dr. Sarah Smith"),
        ("doctor_e2e", &doctor_hash, "doctor", "doctor_e2e@hospital.org", "E2E Doctor"),
        ("nurse", &nurse_hash, "nurse", "nurse@hospital.org", "Nurse John"),
        ("nurse_e2e", &nurse_hash, "nurse", "nurse_e2e@hospital.org", "E2E Nurse"),
        ("patient", &patient_hash, "patient", "patient@hospital.org", "Demo Patient"),
        ("patient_e2e", &patient_hash, "patient", "patient_e2e@hospital.org", "E2E Patient"),
    ];

    for (username, pw_hash, role, email, full_name) in seed_users {
        let user_insert = r#"
            INSERT INTO users (username, hashed_password, role, email, full_name, facility_id, allow_data_collection, is_deleted)
            VALUES ($1, $2, $3, $4, $5, 1, 1, 0)
            ON CONFLICT (username) DO NOTHING
        "#;
        match pool {
            DbPool::Sqlite(p) => {
                let _ = sqlx::query(user_insert)
                    .bind(username).bind(pw_hash).bind(role).bind(email).bind(full_name)
                    .execute(p).await;
            },
            DbPool::Postgres(p) => {
                let _ = sqlx::query(user_insert)
                    .bind(username).bind(pw_hash).bind(role).bind(email).bind(full_name)
                    .execute(p).await;
            },
        };
    }

    Ok(())
}
