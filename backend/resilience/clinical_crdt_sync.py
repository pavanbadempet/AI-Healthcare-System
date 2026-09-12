"""Offline-First Clinical Conflict-Free Replicated Data Types (CRDTs).

Implements state-based delta CRDTs (ORSet, LWW-Element-Set, Vector Clocks) for
decentralized patient chart synchronization across offline ambulances and remote clinics.
Guarantees mathematical Strong Eventual Consistency (SEC) via commutative,
associative, and idempotent join-semilattice merges.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class VectorClock:
    """Vector clock tracking distributed causal history across healthcare nodes."""
    clock: Dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> None:
        """Increment local clock counter for given node."""
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: VectorClock) -> VectorClock:
        """Merge with another vector clock by taking pairwise maximums."""
        all_nodes = set(self.clock.keys()) | set(other.clock.keys())
        merged = {node: max(self.clock.get(node, 0), other.clock.get(node, 0)) for node in all_nodes}
        return VectorClock(clock=merged)

    def is_causally_newer(self, other: VectorClock) -> bool:
        """Return True if self has strictly witnessed all events in other plus more."""
        greater_or_equal = all(self.clock.get(k, 0) >= v for k, v in other.clock.items())
        strictly_greater = any(self.clock.get(k, 0) > other.clock.get(k, 0) for k in self.clock)
        return greater_or_equal and strictly_greater

    def to_dict(self) -> Dict[str, int]:
        return dict(self.clock)

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> VectorClock:
        return cls(clock=dict(data or {}))


@dataclass(frozen=True)
class ORSetElement:
    """Tagged element within an Observed-Remove Set (ORSet)."""
    value: str
    tag: str


class ORSet:
    """Observed-Remove Set (ORSet) CRDT.

    Allows concurrent additions and removals of elements without conflicts.
    Additions create unique tags; removals track observed tags in a tombstone set.
    """

    def __init__(
        self,
        add_set: Optional[Set[ORSetElement]] = None,
        remove_set: Optional[Set[ORSetElement]] = None,
    ) -> None:
        self.add_set: Set[ORSetElement] = set(add_set or set())
        self.remove_set: Set[ORSetElement] = set(remove_set or set())

    def add(self, value: str) -> str:
        """Add an element, generating a unique causality tag."""
        tag = uuid.uuid4().hex
        elem = ORSetElement(value=str(value), tag=tag)
        self.add_set.add(elem)
        return tag

    def remove(self, value: str) -> int:
        """Remove all currently observed instances of value by moving tags to remove_set."""
        matching = {elem for elem in self.add_set if elem.value == str(value)}
        self.remove_set.update(matching)
        return len(matching)

    def read(self) -> Set[str]:
        """Read the live elements of the set (adds minus removes)."""
        active_elements = self.add_set - self.remove_set
        return {elem.value for elem in active_elements}

    def merge(self, other: ORSet) -> ORSet:
        """Commutative, associative, idempotent join-semilattice merge."""
        merged_adds = self.add_set | other.add_set
        merged_removes = self.remove_set | other.remove_set
        return ORSet(add_set=merged_adds, remove_set=merged_removes)

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "add_set": [{"value": e.value, "tag": e.tag} for e in sorted(self.add_set, key=lambda x: (x.value, x.tag))],
            "remove_set": [{"value": e.value, "tag": e.tag} for e in sorted(self.remove_set, key=lambda x: (x.value, x.tag))],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ORSet:
        adds = {ORSetElement(value=d["value"], tag=d["tag"]) for d in data.get("add_set", [])}
        removes = {ORSetElement(value=d["value"], tag=d["tag"]) for d in data.get("remove_set", [])}
        return cls(add_set=adds, remove_set=removes)


@dataclass
class LWWRegister:
    """Last-Write-Wins Register with deterministic node tie-breaking."""
    value: Any
    timestamp_us: int
    node_id: str

    def merge(self, other: LWWRegister) -> LWWRegister:
        """Merge by choosing higher timestamp, tie-breaking on lexicographical node_id."""
        if self.timestamp_us > other.timestamp_us:
            return self
        if other.timestamp_us > self.timestamp_us:
            return other
        # Deterministic tie-breaker
        if self.node_id >= other.node_id:
            return self
        return other

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "timestamp_us": self.timestamp_us,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LWWRegister:
        return cls(
            value=data["value"],
            timestamp_us=int(data["timestamp_us"]),
            node_id=str(data["node_id"]),
        )


class ClinicalPatientChartCRDT:
    """Decentralized conflict-free patient chart supporting offline mutations."""

    def __init__(
        self,
        patient_id: str,
        allergies: Optional[ORSet] = None,
        medications: Optional[ORSet] = None,
        vitals: Optional[Dict[str, LWWRegister]] = None,
        clock: Optional[VectorClock] = None,
    ) -> None:
        self.patient_id = patient_id
        self.allergies = allergies or ORSet()
        self.medications = medications or ORSet()
        self.vitals = vitals or {}
        self.clock = clock or VectorClock()

    def add_allergy(self, allergen: str, node_id: str) -> None:
        """Add known drug or environmental allergy."""
        self.allergies.add(allergen)
        self.clock.increment(node_id)

    def remove_allergy(self, allergen: str, node_id: str) -> None:
        """Remove resolved or falsely recorded allergy."""
        self.allergies.remove(allergen)
        self.clock.increment(node_id)

    def add_medication(self, medication: str, node_id: str) -> None:
        """Add active medication regimen."""
        self.medications.add(medication)
        self.clock.increment(node_id)

    def remove_medication(self, medication: str, node_id: str) -> None:
        """Discontinue or remove medication."""
        self.medications.remove(medication)
        self.clock.increment(node_id)

    def record_vital(self, vital_name: str, value: Any, node_id: str, timestamp_us: Optional[int] = None) -> None:
        """Record a physiological vital sign with microsecond timestamp."""
        ts = timestamp_us or int(time.time() * 1_000_000)
        new_reg = LWWRegister(value=value, timestamp_us=ts, node_id=node_id)
        if vital_name in self.vitals:
            self.vitals[vital_name] = self.vitals[vital_name].merge(new_reg)
        else:
            self.vitals[vital_name] = new_reg
        self.clock.increment(node_id)

    def merge(self, other: ClinicalPatientChartCRDT) -> ClinicalPatientChartCRDT:
        """Merge two divergent replicas into a single mathematically converged chart."""
        if self.patient_id != other.patient_id:
            raise ValueError(f"Cannot merge charts of different patients: '{self.patient_id}' vs '{other.patient_id}'")

        merged_allergies = self.allergies.merge(other.allergies)
        merged_medications = self.medications.merge(other.medications)
        merged_clock = self.clock.merge(other.clock)

        all_vitals_keys = set(self.vitals.keys()) | set(other.vitals.keys())
        merged_vitals: Dict[str, LWWRegister] = {}
        for k in all_vitals_keys:
            if k in self.vitals and k in other.vitals:
                merged_vitals[k] = self.vitals[k].merge(other.vitals[k])
            elif k in self.vitals:
                merged_vitals[k] = self.vitals[k]
            else:
                merged_vitals[k] = other.vitals[k]

        return ClinicalPatientChartCRDT(
            patient_id=self.patient_id,
            allergies=merged_allergies,
            medications=merged_medications,
            vitals=merged_vitals,
            clock=merged_clock,
        )

    def snapshot(self) -> Dict[str, Any]:
        """Generate human-readable materialized clinical snapshot."""
        return {
            "patient_id": self.patient_id,
            "active_allergies": sorted(list(self.allergies.read())),
            "active_medications": sorted(list(self.medications.read())),
            "latest_vitals": {k: reg.value for k, reg in self.vitals.items()},
            "vector_clock": self.clock.to_dict(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize full internal CRDT state for wire transport."""
        return {
            "patient_id": self.patient_id,
            "allergies": self.allergies.to_dict(),
            "medications": self.medications.to_dict(),
            "vitals": {k: reg.to_dict() for k, reg in self.vitals.items()},
            "clock": self.clock.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClinicalPatientChartCRDT:
        """Reconstitute full internal CRDT from wire representation."""
        return cls(
            patient_id=data["patient_id"],
            allergies=ORSet.from_dict(data.get("allergies", {})),
            medications=ORSet.from_dict(data.get("medications", {})),
            vitals={k: LWWRegister.from_dict(v) for k, v in data.get("vitals", {}).items()},
            clock=VectorClock.from_dict(data.get("clock", {})),
        )
