"""Clinical Care Protocol & Order Set Version Control Engine (SemVer 2.0.0).

Governs hospital clinical care pathways, order sets, and therapeutic guidelines
through strict semantic versioning, safety linting, multi-stage approval lifecycles,
and unit-scoped canary deployments.
"""

from __future__ import annotations

import datetime
import re
from enum import Enum
from typing import Any, Dict, List, Optional


class ProtocolStatus(str, Enum):
    """Lifecycle progression states for clinical protocols."""

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class SemanticVersion:
    """SemVer 2.0.0 comparator for clinical guidelines."""

    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def parse(cls, version_str: str) -> SemanticVersion:
        """Parse 'MAJOR.MINOR.PATCH' string."""
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str.strip())
        if not m:
            raise ValueError(f"Invalid SemVer string: '{version_str}'. Expected format X.Y.Z")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other: SemanticVersion) -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: SemanticVersion) -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)


class ProtocolStep:
    """Individual clinical order, medication instruction, or diagnostic milestone."""

    def __init__(
        self,
        step_id: str,
        name: str,
        action_type: str,
        parameters: Dict[str, Any],
        time_limit_minutes: Optional[int] = None,
    ) -> None:
        self.step_id = step_id
        self.name = name
        self.action_type = action_type  # MEDICATION_ORDER, LAB_DRAW, VITAL_CHECK, MONITORING
        self.parameters = parameters
        self.time_limit_minutes = time_limit_minutes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "time_limit_minutes": self.time_limit_minutes,
        }


class ClinicalProtocol:
    """Versioned clinical care guideline."""

    def __init__(
        self,
        protocol_id: str,
        title: str,
        version: SemanticVersion,
        steps: List[ProtocolStep],
        author_id: str,
        status: ProtocolStatus = ProtocolStatus.DRAFT,
        canary_units: Optional[List[str]] = None,
        approvers: Optional[List[str]] = None,
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.protocol_id = protocol_id
        self.title = title
        self.version = version
        self.steps = steps
        self.author_id = author_id
        self.status = status
        self.canary_units = canary_units or []
        self.approvers = approvers or []
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "title": self.title,
            "version": str(self.version),
            "status": self.status.value,
            "canary_units": self.canary_units,
            "approvers": self.approvers,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProtocolSafetyLinter:
    """Pre-deployment verification suite for clinical order sets."""

    @staticmethod
    def lint(protocol: ClinicalProtocol) -> List[str]:
        """Verify protocol contains no missing parameters, dosage violations, or conflicting steps."""
        issues: List[str] = []

        if not protocol.steps:
            issues.append("Protocol contains zero actionable clinical steps")

        seen_steps = set()
        for idx, step in enumerate(protocol.steps):
            if step.step_id in seen_steps:
                issues.append(f"Duplicate step ID '{step.step_id}' at index {idx}")
            seen_steps.add(step.step_id)

            # Check medication orders for dosage bounds
            if step.action_type == "MEDICATION_ORDER":
                p = step.parameters
                dose = p.get("dose")
                max_dose = p.get("max_dose")
                if dose is not None and max_dose is not None and dose > max_dose:
                    issues.append(
                        f"Step '{step.name}' dose {dose} exceeds ceiling max_dose {max_dose}"
                    )
                if not p.get("route"):
                    issues.append(f"Step '{step.name}' missing administration route")

        return issues


class ProtocolVCSEngine:
    """Repository managing version history, promotions, and canary deployments."""

    def __init__(self) -> None:
        # (protocol_id, version_str) -> ClinicalProtocol
        self._protocols: Dict[tuple[str, str], ClinicalProtocol] = {}

    def create_protocol(
        self,
        protocol_id: str,
        title: str,
        version_str: str,
        steps_data: List[Dict[str, Any]],
        author_id: str,
    ) -> ClinicalProtocol:
        """Register a new protocol draft under version control."""
        ver = SemanticVersion.parse(version_str)
        key = (protocol_id, str(ver))
        if key in self._protocols:
            raise ValueError(f"Protocol '{protocol_id}' version '{ver}' already exists")

        steps: List[ProtocolStep] = []
        for s in steps_data:
            steps.append(
                ProtocolStep(
                    step_id=s.get("step_id", s.get("name", "step")),
                    name=s.get("name", "Step"),
                    action_type=s.get("action_type", "MEDICATION_ORDER"),
                    parameters=s.get("parameters", {}),
                    time_limit_minutes=s.get("time_limit_minutes"),
                )
            )

        proto = ClinicalProtocol(
            protocol_id=protocol_id,
            title=title,
            version=ver,
            steps=steps,
            author_id=author_id,
            status=ProtocolStatus.DRAFT,
        )

        self._protocols[key] = proto
        return proto

    def transition_status(
        self,
        protocol_id: str,
        version_str: str,
        target_status: ProtocolStatus | str,
        user_id: str,
        canary_units: Optional[List[str]] = None,
    ) -> ClinicalProtocol:
        """Transition protocol through lifecycle stages with safety checks."""
        key = (protocol_id, version_str)
        proto = self._protocols.get(key)
        if not proto:
            raise KeyError(f"Protocol '{protocol_id}' version '{version_str}' not found")

        target = ProtocolStatus(target_status) if isinstance(target_status, str) else target_status

        # If promoting to STAGED or ACTIVE, run safety linter
        if target in (ProtocolStatus.STAGED, ProtocolStatus.ACTIVE):
            lint_errors = ProtocolSafetyLinter.lint(proto)
            if lint_errors:
                raise ValueError(f"Safety linter blocked promotion: {'; '.join(lint_errors)}")

        # If activating hospital-wide, supersede previous active versions
        if target == ProtocolStatus.ACTIVE:
            for (p_id, v_str), other in self._protocols.items():
                if p_id == protocol_id and v_str != version_str and other.status == ProtocolStatus.ACTIVE:
                    other.status = ProtocolStatus.DEPRECATED
                    other.updated_at = datetime.datetime.now(datetime.timezone.utc)

        if user_id not in proto.approvers:
            proto.approvers.append(user_id)

        proto.status = target
        if canary_units is not None:
            proto.canary_units = canary_units

        proto.updated_at = datetime.datetime.now(datetime.timezone.utc)
        return proto

    def resolve_effective_protocol(
        self,
        protocol_id: str,
        unit_name: Optional[str] = None,
    ) -> Optional[ClinicalProtocol]:
        """Resolve the effective protocol for a specific hospital unit.

        Prioritizes STAGED canary deployments for targeted units, otherwise returns hospital-wide ACTIVE.
        """
        all_versions = [p for (p_id, _), p in self._protocols.items() if p_id == protocol_id]
        if not all_versions:
            return None

        # 1. Check for canary deployment targeting this unit
        if unit_name:
            for p in all_versions:
                if p.status == ProtocolStatus.STAGED and unit_name in p.canary_units:
                    return p

        # 2. Return hospital-wide ACTIVE version
        active_versions = [p for p in all_versions if p.status == ProtocolStatus.ACTIVE]
        if active_versions:
            # Pick highest version
            active_versions.sort(key=lambda p: p.version, reverse=True)
            return active_versions[0]

        return None

    def diff_protocols(
        self,
        protocol_id: str,
        version_v1: str,
        version_v2: str,
    ) -> Dict[str, Any]:
        """Compute structural delta between two protocol versions."""
        p1 = self._protocols.get((protocol_id, version_v1))
        p2 = self._protocols.get((protocol_id, version_v2))

        if not p1 or not p2:
            raise KeyError(f"One or both versions ({version_v1}, {version_v2}) not found")

        s1_map = {s.step_id: s for s in p1.steps}
        s2_map = {s.step_id: s for s in p2.steps}

        added_steps = [s.to_dict() for sid, s in s2_map.items() if sid not in s1_map]
        removed_steps = [s.to_dict() for sid, s in s1_map.items() if sid not in s2_map]
        modified_steps: List[Dict[str, Any]] = []

        for sid, s2 in s2_map.items():
            if sid in s1_map:
                s1 = s1_map[sid]
                if s1.parameters != s2.parameters or s1.time_limit_minutes != s2.time_limit_minutes:
                    modified_steps.append({
                        "step_id": sid,
                        "from_parameters": s1.parameters,
                        "to_parameters": s2.parameters,
                        "from_time_limit": s1.time_limit_minutes,
                        "to_time_limit": s2.time_limit_minutes,
                    })

        return {
            "protocol_id": protocol_id,
            "v1": version_v1,
            "v2": version_v2,
            "added_steps": added_steps,
            "removed_steps": removed_steps,
            "modified_steps": modified_steps,
        }

    def clear(self) -> None:
        """Reset internal store (for testing)."""
        self._protocols.clear()
