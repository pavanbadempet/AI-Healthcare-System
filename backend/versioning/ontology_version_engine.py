"""Semantic Medical Ontology & Terminology Version Control Engine.

Governs multi-release medical terminologies (SNOMED-CT, LOINC, ICD-10, ICD-11, RxNorm),
detects concept retirements in active patient charts, and synthesizes non-destructive
migration patches with clinical review safeguards.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional


class TerminologySystem(str, Enum):
    """Supported clinical terminology standards."""

    SNOMED_CT = "SNOMED_CT"
    LOINC = "LOINC"
    ICD_10 = "ICD_10"
    ICD_11 = "ICD_11"
    RXNORM = "RXNORM"


class ConceptStatus(str, Enum):
    """Standardized lifecycle status of medical ontology codes."""

    CURRENT = "CURRENT"
    RETIRED = "RETIRED"
    SUPERSEDED = "SUPERSEDED"
    AMBIGUOUS = "AMBIGUOUS"


class MedicalConcept:
    """Individual coded clinical concept in a specific terminology release."""

    def __init__(
        self,
        system: TerminologySystem | str,
        code: str,
        display: str,
        release_version: str,
        status: ConceptStatus | str = ConceptStatus.CURRENT,
        replacement_code: Optional[str] = None,
        replacement_display: Optional[str] = None,
    ) -> None:
        self.system = TerminologySystem(system) if isinstance(system, str) else system
        self.code = code
        self.display = display
        self.release_version = release_version
        self.status = ConceptStatus(status) if isinstance(status, str) else status
        self.replacement_code = replacement_code
        self.replacement_display = replacement_display

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system.value,
            "code": self.code,
            "display": self.display,
            "release_version": self.release_version,
            "status": self.status.value,
            "replacement_code": self.replacement_code,
            "replacement_display": self.replacement_display,
        }


class DeprecationFinding:
    """Detection of an obsolete or retired medical code in an active clinical record."""

    def __init__(
        self,
        system: str,
        obsolete_code: str,
        concept_name: str,
        status: str,
        recommended_code: Optional[str],
        recommended_display: Optional[str],
        clinical_domain: str,  # 'conditions', 'medications', 'labs'
    ) -> None:
        self.system = system
        self.obsolete_code = obsolete_code
        self.concept_name = concept_name
        self.status = status
        self.recommended_code = recommended_code
        self.recommended_display = recommended_display
        self.clinical_domain = clinical_domain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system,
            "obsolete_code": self.obsolete_code,
            "concept_name": self.concept_name,
            "status": self.status,
            "recommended_code": self.recommended_code,
            "recommended_display": self.recommended_display,
            "clinical_domain": self.clinical_domain,
        }


class OntologyVersionEngine:
    """Repository of terminology releases and chart deprecation scanner."""

    def __init__(self) -> None:
        # (system_str, code, release_version) -> MedicalConcept
        self._concepts: Dict[tuple[str, str, str], MedicalConcept] = {}
        self._seed_standard_releases()

    def _seed_standard_releases(self) -> None:
        """Seed representative active and retired medical concepts across releases."""
        # 2026-01 Baseline release
        self.register_concept(
            system=TerminologySystem.ICD_10,
            code="I21.0",
            display="ST elevation myocardial infarction (STEMI) of anterior wall",
            release_version="2026-01",
            status=ConceptStatus.CURRENT,
        )
        self.register_concept(
            system=TerminologySystem.SNOMED_CT,
            code="38341003",
            display="Hypertensive disorder",
            release_version="2026-01",
            status=ConceptStatus.CURRENT,
        )

        # 2026-06 Updated release with deprecations / migrations
        # Example: Retired obsolete SNOMED code mapped to specific modern concept
        self.register_concept(
            system=TerminologySystem.SNOMED_CT,
            code="59621000",
            display="Essential hypertension (legacy code)",
            release_version="2026-06",
            status=ConceptStatus.RETIRED,
            replacement_code="38341003",
            replacement_display="Hypertensive disorder, systemic essential",
        )
        # Example: LOINC test code superseded by improved assay
        self.register_concept(
            system=TerminologySystem.LOINC,
            code="2951-2",
            display="Sodium [Moles/volume] in Serum or Plasma (Legacy Flame Photometry)",
            release_version="2026-06",
            status=ConceptStatus.SUPERSEDED,
            replacement_code="2947-0",
            replacement_display="Sodium [Moles/volume] in Serum or Plasma by Ion-selective membrane",
        )

    def register_concept(
        self,
        system: TerminologySystem | str,
        code: str,
        display: str,
        release_version: str,
        status: ConceptStatus | str = ConceptStatus.CURRENT,
        replacement_code: Optional[str] = None,
        replacement_display: Optional[str] = None,
    ) -> MedicalConcept:
        """Register a concept code within a specific release version."""
        concept = MedicalConcept(
            system=system,
            code=code,
            display=display,
            release_version=release_version,
            status=status,
            replacement_code=replacement_code,
            replacement_display=replacement_display,
        )
        key = (concept.system.value, code, release_version)
        self._concepts[key] = concept
        return concept

    def get_concept(
        self,
        system: TerminologySystem | str,
        code: str,
        release_version: str,
    ) -> Optional[MedicalConcept]:
        sys_str = system.value if isinstance(system, TerminologySystem) else system
        return self._concepts.get((sys_str, code, release_version))

    def scan_chart_for_deprecations(
        self,
        chart: Dict[str, Any],
        target_release: str = "2026-06",
    ) -> List[DeprecationFinding]:
        """Inspect patient chart conditions and labs for obsolete concepts in target release."""
        findings: List[DeprecationFinding] = []

        # Check conditions
        conditions = chart.get("conditions", {})
        for c_id, cond in conditions.items():
            code = cond.get("code")
            if not code:
                continue

            # Look up against SNOMED_CT and ICD_10
            for sys_name in [TerminologySystem.SNOMED_CT.value, TerminologySystem.ICD_10.value]:
                concept = self._concepts.get((sys_name, code, target_release))
                if concept and concept.status in (ConceptStatus.RETIRED, ConceptStatus.SUPERSEDED):
                    findings.append(
                        DeprecationFinding(
                            system=sys_name,
                            obsolete_code=code,
                            concept_name=cond.get("name", concept.display),
                            status=concept.status.value,
                            recommended_code=concept.replacement_code,
                            recommended_display=concept.replacement_display,
                            clinical_domain="conditions",
                        )
                    )

        # Check labs
        labs = chart.get("labs", {})
        for l_name, lab in labs.items():
            code = lab.get("code") or lab.get("loinc")
            if not code:
                continue

            concept = self._concepts.get((TerminologySystem.LOINC.value, code, target_release))
            if concept and concept.status in (ConceptStatus.RETIRED, ConceptStatus.SUPERSEDED):
                findings.append(
                    DeprecationFinding(
                        system=TerminologySystem.LOINC.value,
                        obsolete_code=code,
                        concept_name=l_name,
                        status=concept.status.value,
                        recommended_code=concept.replacement_code,
                        recommended_display=concept.replacement_display,
                        clinical_domain="labs",
                    )
                )

        return findings

    def generate_migration_patch(
        self,
        chart: Dict[str, Any],
        findings: List[DeprecationFinding],
    ) -> Dict[str, Any]:
        """Synthesize a non-destructive patch proposal to update obsolete concept codes."""
        patch_operations: List[Dict[str, Any]] = []

        for f in findings:
            if f.recommended_code:
                patch_operations.append({
                    "op": "REPLACE_CODE",
                    "domain": f.clinical_domain,
                    "target_identifier": f.obsolete_code,
                    "new_code": f.recommended_code,
                    "new_display": f.recommended_display,
                    "system": f.system,
                    "rationale": f"Ontology version upgrade to resolve {f.status} concept",
                })

        return {
            "patient_id": chart.get("patient_id"),
            "target_release": "2026-06",
            "findings_count": len(findings),
            "patch_operations": patch_operations,
            "requires_clinician_signoff": True,
        }

    def clear(self) -> None:
        """Reset internal store (for testing)."""
        self._concepts.clear()
        self._seed_standard_releases()
