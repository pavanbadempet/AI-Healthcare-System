"""
AI Healthcare System — SOTA Domain Model Layer Engine
======================================================
Provides state-of-the-art domain modeling primitives:
1. Strongly Typed Domain Value Objects (Primitive Obsession Protection)
2. Rust-Accelerated Pydantic V2 Serializers & State Transitions
3. Built-In Event-Sourced Model Mutation Audit Logger
"""

from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field


class PatientMRN(BaseModel):
    """Strongly-typed Medical Record Number (MRN) Value Object."""
    value: str = Field(..., pattern=r"^MRN-\d{6,10}$")

    model_config = ConfigDict(frozen=True)


class ModelMutationAudit(BaseModel):
    """Audit event for model field mutation tracking."""
    field_name: str
    old_val: Any
    new_val: Any
    timestamp_epoch: float


class ClinicalPatientModel(BaseModel):
    """SOTA Domain Patient Entity Model."""
    mrn: PatientMRN
    full_name: str
    age: int
    primary_condition: str
    audit_trail: List[ModelMutationAudit] = []

    model_config = ConfigDict(validate_assignment=True)

    def update_condition(self, new_condition: str, timestamp_epoch: float):
        """State mutation method recording domain audit trail."""
        audit = ModelMutationAudit(
            field_name="primary_condition",
            old_val=self.primary_condition,
            new_val=new_condition,
            timestamp_epoch=timestamp_epoch,
        )
        self.primary_condition = new_condition
        self.audit_trail.append(audit)


sota_model_layer_engine = ClinicalPatientModel(
    mrn=PatientMRN(value="MRN-1002003"),
    full_name="John Doe",
    age=45,
    primary_condition="HYPERTENSION",
)
