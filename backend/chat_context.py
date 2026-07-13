"""
AI Healthcare System — Medical RAG Context Builder

Analyzes patient questions and queries relevant DB tables to build
rich, structured context for LLM-powered medical Q&A.

Architecture:
  1. Parse question for medical intent and mentioned conditions
  2. Query patient profile, health records, predictions, chat history
  3. Assemble structured context sections within token budget
  4. Return (context_string, sources_list) for citation tracking

Inspired by Universe Dex chat_context.py, adapted for healthcare domain.
"""

import logging
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHARS = 6000  # Conservative for smaller models
GLOBAL_RAG_ROLES = {"doctor", "admin"}
VALID_RAG_SCOPES = {"patient", "global", "guidelines"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _normalize_rag_scope(rag_scope: Optional[str], user: models.User) -> str:
    """Normalize client RAG scope while enforcing role-based global access."""
    scope = (rag_scope or "patient").strip().lower()
    if scope == "all":
        scope = "global"
    if scope not in VALID_RAG_SCOPES:
        scope = "patient"

    role = (getattr(user, "role", None) or "patient").lower()
    if scope == "global" and role not in GLOBAL_RAG_ROLES:
        return "patient"

    return scope


def _build_patient_profile(user: models.User) -> str:
    """Build a structured patient profile from user data."""
    if user.role and user.role != "patient":
        return f"### Staff Member: {user.full_name or user.username} (Role: {user.role})\nNote: You are logged in as a staff member. Please use the 'Global Hospital Database' scope to search anonymized historical cases."

    lines = [f"### Patient: {user.full_name or user.username}"]

    identity = []
    if user.gender:
        identity.append(f"Gender: {user.gender}")
    if user.dob:
        identity.append(f"DOB: {user.dob}")
    if user.blood_type:
        identity.append(f"Blood Type: {user.blood_type}")
    if identity:
        lines.append(", ".join(identity))

    physical = []
    if user.height:
        physical.append(f"Height: {user.height}")
    if user.weight:
        physical.append(f"Weight: {user.weight}")
    if physical:
        lines.append("Physical: " + ", ".join(physical))

    lifestyle = []
    if hasattr(user, 'diet') and user.diet:
        lifestyle.append(f"Diet: {user.diet}")
    if hasattr(user, 'activity_level') and user.activity_level:
        lifestyle.append(f"Activity: {user.activity_level}")
    if hasattr(user, 'sleep_hours') and user.sleep_hours:
        lifestyle.append(f"Sleep: {user.sleep_hours}h")
    if hasattr(user, 'stress_level') and user.stress_level:
        lifestyle.append(f"Stress: {user.stress_level}")
    if lifestyle:
        lines.append("Lifestyle: " + ", ".join(lifestyle))

    if hasattr(user, 'about_me') and user.about_me:
        lines.append(f"About: {user.about_me[:200]}")

    return "\n".join(lines)


def _build_health_records_context(
    db: Session, user_id: int, record_type: Optional[str] = None, limit: int = 10
) -> tuple[str, list[dict]]:
    """Build context from health records."""
    query = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == user_id
    )
    if record_type:
        query = query.filter(models.HealthRecord.record_type == record_type)
    records = query.order_by(models.HealthRecord.timestamp.desc()).limit(limit).all()

    if not records:
        return "", []

    sources = []
    lines = ["### Recent Health Records"]
    for r in records:
        timestamp = r.timestamp.strftime("%Y-%m-%d") if r.timestamp else "Unknown"
        lines.append(f"  [{timestamp}] {r.record_type}: {r.prediction}")
        sources.append({
            "type": "health_record",
            "name": f"{r.record_type} ({timestamp})",
            "id": r.id,
        })

    return "\n".join(lines), sources


def _build_prediction_context(question: str, db: Session, user_id: int) -> tuple[str, list[dict]]:
    """Pull prediction-specific context if the question mentions a condition."""
    q = _normalize(question)
    sources = []
    lines = []

    # Map keywords to record types
    condition_map = {
        "diabetes": "diabetes",
        "glucose": "diabetes",
        "blood sugar": "diabetes",
        "heart": "heart",
        "cardiac": "heart",
        "cardiovascular": "heart",
        "liver": "liver",
        "hepatic": "liver",
        "kidney": "kidney",
        "renal": "kidney",
        "lung": "lungs",
        "pulmonary": "lungs",
        "respiratory": "lungs",
    }

    matched_types = set()
    for keyword, record_type in condition_map.items():
        if keyword in q:
            matched_types.add(record_type)

    for record_type in matched_types:
        ctx, srcs = _build_health_records_context(db, user_id, record_type=record_type, limit=5)
        if ctx:
            lines.append(ctx)
            sources.extend(srcs)

    return "\n\n".join(lines), sources


def _build_chat_history_context(db: Session, user_id: int, limit: int = 5) -> str:
    """Build context from recent chat history."""
    try:
        logs = (
            db.query(models.ChatLog)
            .filter(models.ChatLog.user_id == user_id)
            .order_by(models.ChatLog.timestamp.desc())
            .limit(limit * 2)  # Get pairs
            .all()
        )
    except Exception:
        return ""

    if not logs:
        return ""

    logs.reverse()
    lines = ["### Recent Conversation"]
    for log in logs[-limit * 2:]:
        role = "Patient" if log.role == "user" else "AI"
        content = (log.content or "")[:150]
        lines.append(f"  {role}: {content}")

    return "\n".join(lines)


def _build_general_stats_context(question: str, db: Session, user_id: int) -> str:
    """Pull general health stats if the question asks about trends or summaries."""
    q = _normalize(question)
    lines = []

    if any(w in q for w in ("trend", "history", "summary", "overview", "progress", "improve")):
        records = (
            db.query(models.HealthRecord)
            .filter(models.HealthRecord.user_id == user_id)
            .order_by(models.HealthRecord.timestamp.asc())
            .all()
        )
        if records:
            # Count by type
            type_counts: dict[str, int] = {}
            for r in records:
                type_counts[r.record_type] = type_counts.get(r.record_type, 0) + 1

            lines.append("### Health Summary")
            lines.append(f"  Total checkups: {len(records)}")
            for rtype, count in type_counts.items():
                lines.append(f"  {rtype}: {count} records")

            # Most recent of each type
            seen_types: set[str] = set()
            lines.append("  Latest results:")
            for r in reversed(records):
                if r.record_type not in seen_types:
                    seen_types.add(r.record_type)
                    timestamp = r.timestamp.strftime("%Y-%m-%d") if r.timestamp else "?"
                    lines.append(f"    {r.record_type} [{timestamp}]: {r.prediction}")

    return "\n".join(lines)


def _scope_health_records_to_user_facility(query, user: models.User):
    if user.facility_id is None:
        return query
    return query.join(models.User, models.HealthRecord.user_id == models.User.id).filter(
        models.User.facility_id == user.facility_id
    )


def _build_global_rag_context(
    db: Session,
    question: str,
    user: models.User,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Hospital-wide Global RAG Search (Anonymized).
    Finds historical cases matching conditions mentioned in the query.
    """
    q = _normalize(question)
    sources = []
    lines = ["### Global Hospital Database (Anonymized Historical Cases)"]

    condition_map = {
        "diabetes": "diabetes", "glucose": "diabetes", "sugar": "diabetes",
        "heart": "heart", "cardiac": "heart", "cardiovascular": "heart",
        "liver": "liver", "hepatic": "liver", "kidney": "kidney", "renal": "kidney",
        "lung": "lungs", "pulmonary": "lungs", "respiratory": "lungs",
    }

    matched_types = set()
    for keyword, record_type in condition_map.items():
        if keyword in q:
            matched_types.add(record_type)

    if not matched_types:
        # Fallback to general historical statistics if no specific disease mentioned
        total_records = _scope_health_records_to_user_facility(
            db.query(models.HealthRecord),
            user,
        ).count()
        lines.append(f"System has indexed {total_records} historical health records across all departments.")
        lines.append("No specific disease keyword detected for cross-patient similarity matching.")
        return "\n".join(lines), sources

    for record_type in matched_types:
        query = db.query(models.HealthRecord).filter(models.HealthRecord.record_type == record_type)
        records = (
            _scope_health_records_to_user_facility(query, user)
                .order_by(models.HealthRecord.timestamp.desc())
                .limit(10)
                .all()
        )
        if records:
            lines.append(f"\n#### Historical {record_type.capitalize()} Cases")
            for r in records:
                timestamp = r.timestamp.strftime("%Y-%m-%d") if r.timestamp else "Unknown"
                # Strip PII completely, only show the diagnosis/prediction and time
                lines.append(f"  - [Case {r.id}] ({timestamp}): {r.prediction}")
                sources.append({"type": "global_record", "name": f"Anonymized {record_type} Case", "id": r.id})

    return "\n".join(lines), sources


def build_chat_context(
    db: Session, question: str, user: models.User, rag_scope: Optional[str] = "patient"
) -> tuple[str, list[dict[str, Any]]]:
    """
    Build RAG context for a chat question with Role-Based Governance.

    Returns (context_string, sources_list).
    """
    rag_scope = _normalize_rag_scope(rag_scope, user)

    if rag_scope == "global":
        global_ctx, global_sources = _build_global_rag_context(db, question, user)
        # Always include chat history for context continuity even in global mode
        chat_ctx = _build_chat_history_context(db, user.id, limit=3)
        combined = f"{global_ctx}\n\n{chat_ctx}"
        if len(combined) > MAX_CONTEXT_CHARS:
            combined = combined[:MAX_CONTEXT_CHARS] + "\n...(truncated)"
        return combined, global_sources

    # Standard Patient-Scoped RAG
    sources: list[dict[str, Any]] = []
    sections: list[str] = []

    # 1. Patient profile
    profile = _build_patient_profile(user)
    sections.append(profile)
    sources.append({"type": "patient_profile", "name": user.full_name or user.username, "id": user.id})

    # 2. Condition-specific records
    pred_ctx, pred_sources = _build_prediction_context(question, db, user.id)
    if pred_ctx:
        sections.append(pred_ctx)
        sources.extend(pred_sources)

    # 3. General health records (if no specific condition matched)
    if not pred_ctx:
        rec_ctx, rec_sources = _build_health_records_context(db, user.id, limit=8)
        if rec_ctx:
            sections.append(rec_ctx)
            sources.extend(rec_sources)

    # 4. General stats if asking about trends
    stats_ctx = _build_general_stats_context(question, db, user.id)
    if stats_ctx:
        sections.append(stats_ctx)

    # 5. Recent chat history for continuity
    chat_ctx = _build_chat_history_context(db, user.id, limit=3)
    if chat_ctx:
        sections.append(chat_ctx)

    # Combine and truncate
    full_context = "\n\n".join(sections)
    if len(full_context) > MAX_CONTEXT_CHARS:
        full_context = full_context[:MAX_CONTEXT_CHARS] + "\n...(truncated)"

    return full_context, sources


def get_suggested_questions(db: Session, user: models.User) -> list[str]:
    """Return starter questions based on the patient's health data."""
    suggestions = []

    # Check what records exist
    records = (
        db.query(models.HealthRecord)
        .filter(models.HealthRecord.user_id == user.id)
        .order_by(models.HealthRecord.timestamp.desc())
        .limit(20)
        .all()
    )

    record_types = set(r.record_type for r in records)

    if "diabetes" in record_types:
        suggestions.append("How are my diabetes checkup results trending?")
        suggestions.append("What can I do to improve my blood sugar levels?")
    if "heart" in record_types:
        suggestions.append("Summarize my heart health history.")
        suggestions.append("What lifestyle changes help with heart disease prevention?")
    if "liver" in record_types:
        suggestions.append("What do my liver test results indicate?")

    # Generic suggestions
    suggestions.extend([
        "Give me an overview of my health records.",
        "What preventive screenings should I consider?",
        "How can I improve my overall health?",
        "What are the early warning signs of diabetes?",
        "Explain the risk factors for heart disease.",
    ])

    return suggestions[:8]
