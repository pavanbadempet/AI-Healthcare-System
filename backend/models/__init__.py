"""
Backward-compatible models package.

Re-exports every ORM class so existing code like:
    from backend import models
    models.User
    from backend.models import Base, User, Appointment
continues to work unchanged.
"""
# noqa: F401 — intentional re-exports for backward compatibility

from ..database import Base  # noqa: F401 — re-exported for backward compat

# Appointments domain
from .appointments import Appointment

# Auth domain
from .auth import User

# Billing domain
from .billing import BillableService, BillingPayment, Invoice, InvoiceLineItem

# Clinical domain
from .clinical import (
    CareEvent,
    ClinicalOrder,
    DiagnosticResult,
    MonitoringSignal,
    VitalObservation,
    SparkStreamingMetrics,
)

# Discharge domain
from .discharge import DischargeSummary

# Hospital domain
from .hospital import Admission, Bed, Department, Encounter, HospitalFacility

# Interoperability domain
from .interoperability import (
    ABDMConsentEvent,
    InteroperabilityConsent,
    InteroperabilityExport,
    InteroperabilityExportProfile,
)

# Nursing domain
from .nursing import NursingTask

# Pharmacy domain
from .pharmacy import DispenseRecord, MedicationInventory, Prescription, PrescriptionItem

# Records domain
from .records import AuditLog, ChatLog, HealthRecord

__all__ = [
    "Base",
    # Auth
    "User",
    # Records
    "HealthRecord",
    "ChatLog",
    "AuditLog",
    # Appointments
    "Appointment",
    # Hospital
    "HospitalFacility",
    "Department",
    "Bed",
    "Encounter",
    "Admission",
    # Clinical
    "ClinicalOrder",
    "CareEvent",
    "VitalObservation",
    "MonitoringSignal",
    "DiagnosticResult",
    "SparkStreamingMetrics",
    # Pharmacy
    "MedicationInventory",
    "Prescription",
    "PrescriptionItem",
    "DispenseRecord",
    # Billing
    "BillableService",
    "Invoice",
    "InvoiceLineItem",
    "BillingPayment",
    # Discharge
    "DischargeSummary",
    # Nursing
    "NursingTask",
    # Interoperability
    "InteroperabilityConsent",
    "ABDMConsentEvent",
    "InteroperabilityExportProfile",
    "InteroperabilityExport",
]
