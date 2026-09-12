"""Bi-Temporal Clinical Modeling Engine (ISO/IEC 9075:2011).

Provides dual-axis temporal tracking separating:
- Valid Time [VT_start, VT_end): When the medical condition/event was clinically true in the patient.
- Transaction Time [TT_start, TT_end): When the medical record was recorded/known to the EHR system.

Eliminates the 'retroactive knowledge' paradox in medical audits and legal discovery.
"""

from __future__ import annotations

import datetime
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BiTemporalRecord:
    """Represents an immutable clinical fact bounded in two temporal dimensions."""

    record_id: str
    entity_type: str  # e.g., 'diagnosis', 'medication', 'vital', 'allergy', 'lab'
    entity_id: str
    patient_id: str
    valid_from: datetime.datetime
    valid_to: Optional[datetime.datetime]  # None means open-ended (currently valid)
    transaction_from: datetime.datetime
    transaction_to: Optional[datetime.datetime]  # None means open-ended (currently believed true by system)
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active_at(
        self,
        valid_time: datetime.datetime,
        transaction_time: datetime.datetime,
    ) -> bool:
        """Evaluate if this record was active in clinical reality at valid_time

        according to the state of the EHR system at transaction_time.
        """
        # Ensure tz-aware comparisons or naive comparisons are uniform
        vt = self._normalize_dt(valid_time)
        tt = self._normalize_dt(transaction_time)

        v_from = self._normalize_dt(self.valid_from)
        v_to = self._normalize_dt(self.valid_to) if self.valid_to else None

        t_from = self._normalize_dt(self.transaction_from)
        t_to = self._normalize_dt(self.transaction_to) if self.transaction_to else None

        # Check Transaction Time interval: [transaction_from, transaction_to)
        tt_match = (v_from is not None) and (t_from <= tt)
        if t_to is not None and tt >= t_to:
            tt_match = False

        if not tt_match:
            return False

        # Check Valid Time interval: [valid_from, valid_to)
        vt_match = v_from <= vt
        if v_to is not None and vt >= v_to:
            vt_match = False

        return vt_match

    @staticmethod
    def _normalize_dt(dt: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
        """Normalize datetime to UTC naive for consistent interval arithmetic."""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary with ISO-formatted timestamps."""
        data = asdict(self)
        data["valid_from"] = self.valid_from.isoformat()
        data["valid_to"] = self.valid_to.isoformat() if self.valid_to else None
        data["transaction_from"] = self.transaction_from.isoformat()
        data["transaction_to"] = self.transaction_to.isoformat() if self.transaction_to else None
        return data


class BiTemporalEngine:
    """In-memory ISO/IEC 9075:2011 compliant Bi-Temporal Engine for clinical records."""

    def __init__(self) -> None:
        self._records: List[BiTemporalRecord] = []

    def insert(
        self,
        entity_type: str,
        entity_id: str,
        patient_id: str,
        valid_from: datetime.datetime,
        valid_to: Optional[datetime.datetime],
        payload: Dict[str, Any],
        transaction_time: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BiTemporalRecord:
        """Insert a newly asserted clinical fact into the bi-temporal timeline."""
        t_now = transaction_time or datetime.datetime.now(datetime.timezone.utc)
        record = BiTemporalRecord(
            record_id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            patient_id=patient_id,
            valid_from=valid_from,
            valid_to=valid_to,
            transaction_from=t_now,
            transaction_to=None,
            payload=payload,
            metadata=metadata or {},
        )
        self._records.append(record)
        return record

    def correct(
        self,
        entity_type: str,
        entity_id: str,
        patient_id: str,
        new_valid_from: datetime.datetime,
        new_valid_to: Optional[datetime.datetime],
        new_payload: Dict[str, Any],
        transaction_time: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[BiTemporalRecord], BiTemporalRecord]:
        """Correct an existing record retroactively.

        Closes the currently active record in transaction time and asserts the correction.
        """
        t_now = transaction_time or datetime.datetime.now(datetime.timezone.utc)
        old_record: Optional[BiTemporalRecord] = None

        # Find the active system record for this entity
        for rec in self._records:
            if (
                rec.patient_id == patient_id
                and rec.entity_type == entity_type
                and rec.entity_id == entity_id
                and rec.transaction_to is None
            ):
                rec.transaction_to = t_now
                old_record = rec
                break

        new_record = BiTemporalRecord(
            record_id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            patient_id=patient_id,
            valid_from=new_valid_from,
            valid_to=new_valid_to,
            transaction_from=t_now,
            transaction_to=None,
            payload=new_payload,
            metadata=metadata or {},
        )
        self._records.append(new_record)
        return old_record, new_record

    def revoke(
        self,
        entity_type: str,
        entity_id: str,
        patient_id: str,
        transaction_time: Optional[datetime.datetime] = None,
    ) -> Optional[BiTemporalRecord]:
        """Revoke a record from active system knowledge without deleting historical truth."""
        t_now = transaction_time or datetime.datetime.now(datetime.timezone.utc)
        for rec in self._records:
            if (
                rec.patient_id == patient_id
                and rec.entity_type == entity_type
                and rec.entity_id == entity_id
                and rec.transaction_to is None
            ):
                rec.transaction_to = t_now
                return rec
        return None

    def query_as_of(
        self,
        patient_id: str,
        valid_time: datetime.datetime,
        transaction_time: datetime.datetime,
        entity_type: Optional[str] = None,
    ) -> List[BiTemporalRecord]:
        """Query clinical truth as-of valid_time according to the knowledge base at transaction_time."""
        results: List[BiTemporalRecord] = []
        for rec in self._records:
            if rec.patient_id != patient_id:
                continue
            if entity_type and rec.entity_type != entity_type:
                continue
            if rec.is_active_at(valid_time=valid_time, transaction_time=transaction_time):
                results.append(rec)
        return results

    def query_entity_audit(self, patient_id: str, entity_id: str) -> List[BiTemporalRecord]:
        """Retrieve the complete dual-temporal lifecycle audit for a specific entity."""
        return [
            rec for rec in self._records
            if rec.patient_id == patient_id and rec.entity_id == entity_id
        ]

    def clear(self) -> None:
        """Reset internal records (for testing)."""
        self._records.clear()
