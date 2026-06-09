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

# Auth domain
from .auth import User

# Records domain
from .records import AuditLog, ChatLog, HealthRecord

# Appointments domain
from .appointments import Appointment

# Hospital domain
from .hospital import Admission, Bed, Department, Encounter, HospitalFacility

# Clinical domain
from .clinical import (
    CareEvent,
    ClinicalOrder,
    DiagnosticResult,
    MonitoringSignal,
    VitalObservation,
)

# Pharmacy domain
from .pharmacy import DispenseRecord, MedicationInventory, Prescription, PrescriptionItem

# Billing domain
from .billing import BillableService, BillingPayment, Invoice, InvoiceLineItem

# Discharge domain
from .discharge import DischargeSummary

# Nursing domain
from .nursing import NursingTask

# Interoperability domain
from .interoperability import (
    ABDMConsentEvent,
    InteroperabilityConsent,
    InteroperabilityExport,
    InteroperabilityExportProfile,
)

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
