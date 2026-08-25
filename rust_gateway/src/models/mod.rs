pub mod appointments;
pub mod auth;
pub mod billing;
pub mod clinical;
pub mod consent;
pub mod discharge;
pub mod federated;
pub mod governance;
pub mod hospital;
pub mod intelligence;
pub mod interoperability;
pub mod nursing;
pub mod pharmacy;
pub mod records;
pub mod smart_app;

// Re-export all 46 database models
pub use appointments::{Appointment, AppointmentCreate};
pub use auth::{User, UserCreate};
pub use billing::{BillableService, BillingPayment, InsuranceClaim, Invoice, InvoiceLineItem};
pub use clinical::{
    CareEvent, ClinicalOrder, DiagnosticResult, MonitoringSignal, SparkStreamingMetrics,
    VitalObservation,
};
pub use consent::ConsentRecord;
pub use discharge::DischargeSummary;
pub use federated::{FederatedSyncAudit, ModelFeedback};
pub use governance::{
    ContractViolation, DataCatalogDataset, DataCatalogLineage, FeatureAttributionLog, SchemaContract,
};
pub use hospital::{Admission, Bed, Department, DicomStudy, Encounter, HospitalFacility};
pub use intelligence::{ClinicalAICorrection, ClinicalAlert, PatientInsight};
pub use interoperability::{
    AbdmConsentEvent, AbhaLink, InteroperabilityConsent, InteroperabilityExport,
    InteroperabilityExportProfile,
};
pub use nursing::NursingTask;
pub use pharmacy::{DispenseRecord, MedicationInventory, Prescription, PrescriptionItem};
pub use records::{AuditLog, ChatLog, HealthRecord};
pub use smart_app::{SmartApp, SmartLaunchContext};
