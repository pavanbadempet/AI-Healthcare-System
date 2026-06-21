"""
Backward-compatible schemas package.

Re-exports every Pydantic schema so existing code like:
    from backend import schemas
    schemas.UserCreate
    from backend.schemas import HeartInput, DiabetesInput
continues to work unchanged.
"""
# noqa: F401 — intentional re-exports for backward compatibility

# Auth domain
# Appointments domain
from .appointments import (  # noqa: F401
    AppointmentCreate,
    AppointmentResponse,
    DoctorResponse,
)
from .auth import (  # noqa: F401
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserFullResponse,
    UserProfileUpdate,
    UserResponse,
)

# Billing domain
from .billing import (  # noqa: F401
    BillableServiceCreate,
    BillableServiceResponse,
    BillingPaymentCreate,
    BillingPaymentResponse,
    InvoiceCreate,
    InvoiceLineItemCreate,
    InvoiceLineItemResponse,
    InvoiceResponse,
)

# Clinical domain
from .clinical import (  # noqa: F401
    CareEventResponse,
    ClinicalOrderCreate,
    ClinicalOrderResponse,
    DiagnosticResultCreate,
    DiagnosticResultResponse,
    DiagnosticReviewUpdate,
    MonitoringSignalResponse,
    PatientTimelineResponse,
    VitalObservationCreate,
    VitalObservationResponse,
    VitalSubmissionResponse,
)

# Discharge domain
from .discharge import (  # noqa: F401
    DischargeSummaryCreate,
    DischargeSummaryResponse,
)

# Federated Learning domain
from .federated import (  # noqa: F401
    FederatedSyncAuditResponse,
    FederatedSyncRequest,
    FederatedSyncResponse,
    ModelFeedbackCreate,
    ModelFeedbackResponse,
)

# Hospital domain
from .hospital import (  # noqa: F401
    AdmissionCreate,
    AdmissionResponse,
    BedCreate,
    BedResponse,
    DepartmentCreate,
    DepartmentResponse,
    EncounterCreate,
    EncounterResponse,
    FacilityCreate,
    FacilityResponse,
)

# Clinical Intelligence domain
from .intelligence import (  # noqa: F401
    AlertAcknowledgeRequest,
    ClinicalAlertResponse,
    ExplainabilityResponse,
    PatientInsightResponse,
)

# Interoperability domain
from .interoperability import (  # noqa: F401
    ABDMConsentCallbackCreate,
    ABDMConsentCallbackResponse,
    ABDMConsentRequestCreate,
    InteroperabilityConsentCreate,
    InteroperabilityConsentResponse,
    InteroperabilityExportProfileCreate,
    InteroperabilityExportProfileResponse,
    InteroperabilityExportResponse,
)

# Nursing domain
from .nursing import (  # noqa: F401
    NursingTaskComplete,
    NursingTaskCreate,
    NursingTaskResponse,
)

# Pharmacy domain
from .pharmacy import (  # noqa: F401
    DispenseItemCreate,
    DispensePrescriptionCreate,
    DispenseRecordResponse,
    MedicationInventoryCreate,
    MedicationInventoryResponse,
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionItemResponse,
    PrescriptionResponse,
)

# Prediction domain
from .prediction import (  # noqa: F401
    DiabetesInput,
    HeartInput,
    KidneyInput,
    LiverInput,
    LungInput,
    PredictionReviewCreate,
)

# Records domain
from .records import (  # noqa: F401
    AuditLogResponse,
    ChatLogResponse,
    HealthRecordResponse,
)

# SMART on FHIR domain
from .smart_app import (  # noqa: F401
    SmartAppCreate,
    SmartAppResponse,
    SmartLaunchRequest,
    SmartLaunchResponse,
)
