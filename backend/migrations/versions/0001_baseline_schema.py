"""Baseline schema — create all tables from scratch

This migration captures the full table structure that existed before Alembic
was introduced. It is the root of the migration chain. Running ``alembic
upgrade head`` on a brand-new database will apply this baseline first,
then the incremental migrations that follow.

Existing databases that were created via ``Base.metadata.create_all()``
should stamp this revision without running it:

    alembic stamp 0001_baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-06 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables that form the baseline schema."""

    # ── hospital_facilities (no foreign deps) ─────────────────────────
    op.create_table(
        "hospital_facilities",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("facility_type", sa.String(), nullable=False, server_default="hospital"),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="patient"),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("blood_type", sa.String(), nullable=True),
        sa.Column("dob", sa.String(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("existing_ailments", sa.Text(), nullable=True),
        sa.Column("profile_picture", sa.Text(), nullable=True),
        sa.Column("about_me", sa.Text(), nullable=True),
        sa.Column("diet", sa.String(), nullable=True),
        sa.Column("activity_level", sa.String(), nullable=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("stress_level", sa.String(), nullable=True),
        sa.Column("allow_data_collection", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True, index=True),
        sa.Column("plan_tier", sa.String(), nullable=False, server_default="free"),
        sa.Column("subscription_expiry", sa.DateTime(), nullable=True),
        sa.Column("razorpay_customer_id", sa.String(), nullable=True),
        sa.Column("consultation_fee", sa.Float(), nullable=False, server_default="500.0"),
        sa.Column("specialization", sa.String(), nullable=True),
        sa.Column("psych_profile", sa.Text(), nullable=True),
        sa.Column("doctor_id", sa.Integer(), nullable=True),
    )

    # ── health_records ─────────────────────────────────────────────────
    op.create_table(
        "health_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("record_type", sa.String(), nullable=False),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("prediction", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
    )

    # ── chat_logs ──────────────────────────────────────────────────────
    op.create_table(
        "chat_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
    )

    # ── audit_logs ─────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("details", sa.String(), nullable=True),
    )

    # ── departments ────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("department_type", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── appointments ───────────────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("specialist", sa.String(), nullable=True),
        sa.Column("date_time", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="Scheduled"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled')",
            name="check_appt_status",
        ),
    )

    # ── beds ───────────────────────────────────────────────────────────
    op.create_table(
        "beds",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("bed_number", sa.String(), nullable=False, index=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="available"),
        sa.Column("current_patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── encounters ─────────────────────────────────────────────────────
    op.create_table(
        "encounters",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("encounter_type", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(), nullable=False, server_default="routine"),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )

    # ── admissions ─────────────────────────────────────────────────────
    op.create_table(
        "admissions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("bed_id", sa.Integer(), sa.ForeignKey("beds.id"), nullable=True),
        sa.Column("admitted_at", sa.DateTime(), nullable=True),
        sa.Column("discharged_at", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )

    # ── clinical_orders ────────────────────────────────────────────────
    op.create_table(
        "clinical_orders",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("order_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False, server_default="routine"),
        sa.Column("status", sa.String(), nullable=False, server_default="ordered"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # ── care_events ────────────────────────────────────────────────────
    op.create_table(
        "care_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False, server_default="info"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── vital_observations ─────────────────────────────────────────────
    op.create_table(
        "vital_observations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("recorded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("heart_rate", sa.Float(), nullable=True),
        sa.Column("systolic_bp", sa.Float(), nullable=True),
        sa.Column("diastolic_bp", sa.Float(), nullable=True),
        sa.Column("spo2", sa.Float(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("respiratory_rate", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── monitoring_signals ─────────────────────────────────────────────
    op.create_table(
        "monitoring_signals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("vital_observation_id", sa.Integer(), sa.ForeignKey("vital_observations.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("signal_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default="info"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "vital_observation_id",
            "signal_type",
            name="uq_monitoring_signal_vital_type",
        ),
    )

    # ── diagnostic_results ─────────────────────────────────────────────
    op.create_table(
        "diagnostic_results",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("clinical_orders.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("result_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("abnormal_flag", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="final"),
        sa.Column("review_status", sa.String(), nullable=False, server_default="pending_review"),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── medication_inventory ───────────────────────────────────────────
    op.create_table(
        "medication_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("medication_name", sa.String(), nullable=False, index=True),
        sa.Column("strength", sa.String(), nullable=True),
        sa.Column("form", sa.String(), nullable=True),
        sa.Column("batch_number", sa.String(), nullable=True, index=True),
        sa.Column("quantity_on_hand", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── prescriptions ──────────────────────────────────────────────────
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("diagnosis_context", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("dispensed_at", sa.DateTime(), nullable=True),
    )

    # ── prescription_items ─────────────────────────────────────────────
    op.create_table(
        "prescription_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id"), nullable=True, index=True),
        sa.Column("inventory_id", sa.Integer(), sa.ForeignKey("medication_inventory.id"), nullable=True),
        sa.Column("medication_name", sa.String(), nullable=False),
        sa.Column("dosage", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("duration", sa.String(), nullable=False),
        sa.Column("quantity_prescribed", sa.Float(), nullable=False, server_default="1"),
        sa.Column("quantity_dispensed", sa.Float(), nullable=False, server_default="0"),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
    )

    # ── dispense_records ───────────────────────────────────────────────
    op.create_table(
        "dispense_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("prescription_id", sa.Integer(), sa.ForeignKey("prescriptions.id"), nullable=True, index=True),
        sa.Column("prescription_item_id", sa.Integer(), sa.ForeignKey("prescription_items.id"), nullable=True, index=True),
        sa.Column("inventory_id", sa.Integer(), sa.ForeignKey("medication_inventory.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("dispensed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("quantity_dispensed", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="dispensed"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── billable_services ──────────────────────────────────────────────
    op.create_table(
        "billable_services",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("service_code", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("service_type", sa.String(), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── invoices ───────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("admission_id", sa.Integer(), sa.ForeignKey("admissions.id"), nullable=True, index=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="issued"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("balance_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
    )

    # ── invoice_line_items ─────────────────────────────────────────────
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True, index=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("billable_services.id"), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
    )

    # ── billing_payments ───────────────────────────────────────────────
    op.create_table(
        "billing_payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("collected_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="collected"),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
    )

    # ── discharge_summaries ────────────────────────────────────────────
    op.create_table(
        "discharge_summaries",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("admission_id", sa.Integer(), sa.ForeignKey("admissions.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("diagnosis_summary", sa.Text(), nullable=False),
        sa.Column("hospital_course", sa.Text(), nullable=False),
        sa.Column("medications", sa.Text(), nullable=True),
        sa.Column("follow_up_plan", sa.Text(), nullable=True),
        sa.Column("discharge_instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
    )

    # ── nursing_tasks ──────────────────────────────────────────────────
    op.create_table(
        "nursing_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("assigned_nurse_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("encounter_id", sa.Integer(), sa.ForeignKey("encounters.id"), nullable=True, index=True),
        sa.Column("admission_id", sa.Integer(), sa.ForeignKey("admissions.id"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(), nullable=False, server_default="routine"),
        sa.Column("status", sa.String(), nullable=False, server_default="assigned"),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── interoperability_consents ──────────────────────────────────────
    op.create_table(
        "interoperability_consents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("granted_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("scope", sa.String(), nullable=False, server_default="fhir_bundle_export"),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("recipient_type", sa.String(), nullable=False, server_default="care_team"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("abdm_request_id", sa.String(), nullable=True),
        sa.Column("abdm_consent_id", sa.String(), nullable=True),
        sa.Column("abdm_status", sa.String(), nullable=True),
        sa.Column("abdm_last_event_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── abdm_consent_events ────────────────────────────────────────────
    op.create_table(
        "abdm_consent_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True, index=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("local_consent_id", sa.Integer(), sa.ForeignKey("interoperability_consents.id"), nullable=True, index=True),
        sa.Column("abdm_request_id", sa.String(), nullable=False, index=True),
        sa.Column("abdm_consent_id", sa.String(), nullable=True, index=True),
        sa.Column("event_type", sa.String(), nullable=False, server_default="consent_status"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("local_consent_status", sa.String(), nullable=True),
        sa.Column("hi_types", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("notification_at", sa.DateTime(), nullable=True),
        sa.Column("payload_sha256", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── interoperability_export_profiles ───────────────────────────────
    op.create_table(
        "interoperability_export_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("partner_system", sa.String(), nullable=True),
        sa.Column("resource_types", sa.Text(), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── interoperability_exports ───────────────────────────────────────
    op.create_table(
        "interoperability_exports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("facility_id", sa.Integer(), sa.ForeignKey("hospital_facilities.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("requested_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("consent_id", sa.Integer(), sa.ForeignKey("interoperability_consents.id"), nullable=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("interoperability_export_profiles.id"), nullable=True),
        sa.Column("export_type", sa.String(), nullable=False, server_default="fhir_bundle"),
        sa.Column("resource_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filter_summary", sa.Text(), nullable=True),
        sa.Column("bundle_sha256", sa.String(), nullable=True),
        sa.Column("manifest_signature", sa.String(), nullable=True),
        sa.Column("signature_algorithm", sa.String(), nullable=False, server_default="HMAC-SHA256"),
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop all baseline tables in reverse dependency order."""
    op.drop_table("interoperability_exports")
    op.drop_table("interoperability_export_profiles")
    op.drop_table("abdm_consent_events")
    op.drop_table("interoperability_consents")
    op.drop_table("nursing_tasks")
    op.drop_table("discharge_summaries")
    op.drop_table("billing_payments")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("billable_services")
    op.drop_table("dispense_records")
    op.drop_table("prescription_items")
    op.drop_table("prescriptions")
    op.drop_table("medication_inventory")
    op.drop_table("diagnostic_results")
    op.drop_table("monitoring_signals")
    op.drop_table("vital_observations")
    op.drop_table("care_events")
    op.drop_table("clinical_orders")
    op.drop_table("admissions")
    op.drop_table("encounters")
    op.drop_table("beds")
    op.drop_table("appointments")
    op.drop_table("departments")
    op.drop_table("audit_logs")
    op.drop_table("chat_logs")
    op.drop_table("health_records")
    op.drop_table("users")
    op.drop_table("hospital_facilities")
