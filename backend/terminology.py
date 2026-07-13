"""Static seed terminology catalog for interoperability mapping.

This is not a replacement for a licensed terminology server. It provides a
small PHI-safe coding surface for integration tests, demos, and export mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LOINC_SYSTEM = "http://loinc.org"
SNOMED_SYSTEM = "http://snomed.info/sct"
ICD10_CM_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"
CATALOG_SOURCE = "static_seed_catalog"
STANDARDS_NOTE = (
    "Seed terminology mapping for integration support; validate against the "
    "target hospital terminology service before production exchange."
)


@dataclass(frozen=True)
class TerminologyConcept:
    system: str
    code: str
    display: str
    category: str
    version_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "code": self.code,
            "display": self.display,
            "category": self.category,
            "coding": {
                "system": self.system,
                "code": self.code,
                "display": self.display,
            },
            "source": CATALOG_SOURCE,
            "version_note": self.version_note,
            "standards_note": STANDARDS_NOTE,
            "pii_exposed": False,
        }


SYSTEM_ALIASES = {
    "loinc": LOINC_SYSTEM,
    LOINC_SYSTEM: LOINC_SYSTEM,
    "snomed": SNOMED_SYSTEM,
    "snomedct": SNOMED_SYSTEM,
    "snomed-ct": SNOMED_SYSTEM,
    SNOMED_SYSTEM: SNOMED_SYSTEM,
    "icd10": ICD10_CM_SYSTEM,
    "icd-10": ICD10_CM_SYSTEM,
    "icd10cm": ICD10_CM_SYSTEM,
    "icd-10-cm": ICD10_CM_SYSTEM,
    ICD10_CM_SYSTEM: ICD10_CM_SYSTEM,
}


_CONCEPTS: dict[tuple[str, str], TerminologyConcept] = {
    (LOINC_SYSTEM, "8867-4"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="8867-4",
        display="Heart rate",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "59408-5"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="59408-5",
        display="Oxygen saturation in Arterial blood by Pulse oximetry",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "8310-5"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="8310-5",
        display="Body temperature",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "8480-6"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="8480-6",
        display="Systolic blood pressure",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "8462-4"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="8462-4",
        display="Diastolic blood pressure",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "9279-1"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="9279-1",
        display="Respiratory rate",
        category="vital-sign",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "2339-0"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="2339-0",
        display="Glucose",
        category="laboratory",
        version_note="LOINC seed code",
    ),
    (LOINC_SYSTEM, "4548-4"): TerminologyConcept(
        system=LOINC_SYSTEM,
        code="4548-4",
        display="Hemoglobin A1c",
        category="laboratory",
        version_note="LOINC seed code",
    ),
    (SNOMED_SYSTEM, "44054006"): TerminologyConcept(
        system=SNOMED_SYSTEM,
        code="44054006",
        display="Diabetes mellitus type 2",
        category="condition",
        version_note="SNOMED CT seed code",
    ),
    (SNOMED_SYSTEM, "38341003"): TerminologyConcept(
        system=SNOMED_SYSTEM,
        code="38341003",
        display="Hypertensive disorder",
        category="condition",
        version_note="SNOMED CT seed code",
    ),
    (SNOMED_SYSTEM, "195967001"): TerminologyConcept(
        system=SNOMED_SYSTEM,
        code="195967001",
        display="Asthma",
        category="condition",
        version_note="SNOMED CT seed code",
    ),
    (ICD10_CM_SYSTEM, "E11.9"): TerminologyConcept(
        system=ICD10_CM_SYSTEM,
        code="E11.9",
        display="Type 2 diabetes mellitus without complications",
        category="diagnosis",
        version_note="ICD-10-CM seed code",
    ),
    (ICD10_CM_SYSTEM, "I10"): TerminologyConcept(
        system=ICD10_CM_SYSTEM,
        code="I10",
        display="Essential hypertension",
        category="diagnosis",
        version_note="ICD-10-CM seed code",
    ),
}


def _canonical_system(system: Any) -> str | None:
    if system is None:
        return None
    return SYSTEM_ALIASES.get(str(system).strip().lower())


def _normalize_code(system: str, code: Any) -> str:
    if code is None:
        return ""
    if isinstance(code, float) and code.is_integer():
        code = int(code)
    normalized = str(code).strip()
    if system == ICD10_CM_SYSTEM:
        return normalized.upper()
    return normalized


def lookup_code(system: Any, code: Any) -> dict[str, Any] | None:
    if system is None or code is None:
        return None
    canonical_system = _canonical_system(system)
    if canonical_system is None:
        return None
    concept = _CONCEPTS.get((canonical_system, _normalize_code(canonical_system, code)))
    if concept is None:
        return None
    return concept.to_dict()


def list_supported_systems() -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for system, _ in _CONCEPTS:
        counts[system] = counts.get(system, 0) + 1
    return [
        {
            "system": system,
            "concept_count": counts[system],
            "source": CATALOG_SOURCE,
            "pii_exposed": False,
        }
        for system in sorted(counts)
    ]
