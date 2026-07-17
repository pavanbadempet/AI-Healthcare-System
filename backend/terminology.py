"""Production-grade clinical terminology lookup and search service.

Provides a unified interface to validate and lookup codes against LOINC,
SNOMED CT, ICD-10-CM, and RxNorm standard systems. Integrates NLM RxNorm
APIs and a local SQLite cache for high-performance sub-millisecond retrievals.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

LOINC_SYSTEM = "http://loinc.org"
SNOMED_SYSTEM = "http://snomed.info/sct"
ICD10_CM_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"

CATALOG_SOURCE = "standards_hybrid_catalog"
STANDARDS_NOTE = (
    "Interoperability terminology service utilizing local seed catalogs, "
    "persistent cache, and live NLM RxNav APIs."
)

CACHE_DB = os.environ.get("TERMINOLOGY_CACHE_DB", "terminology_cache.db")


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
    "rxnorm": RXNORM_SYSTEM,
    "rxcui": RXNORM_SYSTEM,
    RXNORM_SYSTEM: RXNORM_SYSTEM,
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


def _init_cache_db():
    """Initializes the SQLite cache file for terminology queries."""
    try:
        conn = sqlite3.connect(CACHE_DB)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "system TEXT, code TEXT, display TEXT, category TEXT, version_note TEXT, "
            "PRIMARY KEY(system, code))"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug("Terminology cache db initialization skipped: %s", e)


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


def _fetch_rxnorm_from_api(code: str) -> Optional[TerminologyConcept]:
    """Retrieve drug properties directly from NLM RxNav REST service."""
    try:
        import requests
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{code}/properties.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            prop = data.get("idAndName", {})
            name = prop.get("name")
            if name:
                return TerminologyConcept(
                    system=RXNORM_SYSTEM,
                    code=code,
                    display=name,
                    category="medication",
                    version_note="NLM RxNav Live Lookup",
                )
    except Exception as e:
        logger.warning("RxNorm API lookup failed for CUI %s: %s", code, e)
    return None


def lookup_code(system: Any, code: Any) -> dict[str, Any] | None:
    """Validate and lookup clinical concepts from seed files, cache, or live API."""
    if system is None or code is None:
        return None
    canonical_system = _canonical_system(system)
    if canonical_system is None:
        return None

    normalized_code = _normalize_code(canonical_system, code)

    # 1. Match static seed concepts
    concept = _CONCEPTS.get((canonical_system, normalized_code))
    if concept:
        return concept.to_dict()

    # 2. Check local database cache
    _init_cache_db()
    try:
        conn = sqlite3.connect(CACHE_DB)
        cur = conn.cursor()
        cur.execute(
            "SELECT display, category, version_note FROM cache WHERE system=? AND code=?",
            (canonical_system, normalized_code)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return TerminologyConcept(
                system=canonical_system,
                code=normalized_code,
                display=row[0],
                category=row[1],
                version_note=row[2]
            ).to_dict()
    except Exception as e:
        logger.debug("Terminology cache query failed: %s", e)

    # 3. Handle live RxNorm validation queries
    if canonical_system == RXNORM_SYSTEM:
        concept = _fetch_rxnorm_from_api(normalized_code)
        if concept:
            # Store in cache
            try:
                conn = sqlite3.connect(CACHE_DB)
                conn.execute(
                    "INSERT OR REPLACE INTO cache (system, code, display, category, version_note) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (concept.system, concept.code, concept.display, concept.category, concept.version_note)
                )
                conn.commit()
                conn.close()
            except Exception as cache_err:
                logger.warning("Failed to store terminology cache record: %s", cache_err)
            return concept.to_dict()

    return None


def list_supported_systems() -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for system, _ in _CONCEPTS:
        counts[system] = counts.get(system, 0) + 1

    # Include cached counts if table exists
    try:
        if os.path.exists(CACHE_DB):
            conn = sqlite3.connect(CACHE_DB)
            cur = conn.cursor()
            cur.execute("SELECT system, count(*) FROM cache GROUP BY system")
            for sys_name, cnt in cur.fetchall():
                counts[sys_name] = counts.get(sys_name, 0) + cnt
            conn.close()
    except Exception:
        pass

    return [
        {
            "system": system,
            "concept_count": counts[system],
            "source": CATALOG_SOURCE,
            "pii_exposed": False,
        }
        for system in sorted(counts)
    ]


def semantic_map_symptoms(text: str) -> list[dict[str, Any]]:
    """Scan a clinical text phrase and map it to standardized concepts."""
    if not text:
        return []
    import re
    tokens = set(re.findall(r"\w+", text.lower()))

    matches = []
    synonyms = {
        "heartrate": {"heart", "rate", "pulse", "bpm"},
        "pulse": {"heart", "rate", "pulse", "bpm"},
        "temp": {"temperature", "temp", "fever", "hot"},
        "fever": {"temperature", "temp", "fever", "hot"},
        "glucose": {"glucose", "sugar", "diabetic", "diabetes"},
        "sugar": {"glucose", "sugar", "diabetic", "diabetes"},
        "diabetes": {"glucose", "sugar", "diabetic", "diabetes"},
        "bp": {"blood", "pressure", "bp", "systolic", "diastolic"},
        "hypertension": {"blood", "pressure", "bp", "systolic", "diastolic", "hypertensive", "hypertension"},
        "asthma": {"asthma", "wheezing", "respiratory", "breath"},
        "respiratory": {"respiratory", "breath", "breathing", "lung", "lungs"},
        "oxygen": {"oxygen", "spo2", "saturation", "pulseox"},
        "spo2": {"oxygen", "spo2", "saturation", "pulseox"}
    }

    expanded_tokens = set(tokens)
    for token in tokens:
        if token in synonyms:
            expanded_tokens.update(synonyms[token])

    # Match against static concepts
    for concept in _CONCEPTS.values():
        display_words = set(re.findall(r"\w+", concept.display.lower()))
        if expanded_tokens.intersection(display_words):
            matches.append(concept.to_dict())

    # Match against cached concepts
    try:
        if os.path.exists(CACHE_DB):
            conn = sqlite3.connect(CACHE_DB)
            cur = conn.cursor()
            cur.execute("SELECT system, code, display, category, version_note FROM cache")
            for sys_name, code_val, disp_val, cat_val, ver_val in cur.fetchall():
                display_words = set(re.findall(r"\w+", disp_val.lower()))
                if expanded_tokens.intersection(display_words):
                    matches.append(TerminologyConcept(
                        system=sys_name,
                        code=code_val,
                        display=disp_val,
                        category=cat_val,
                        version_note=ver_val
                    ).to_dict())
            conn.close()
    except Exception:
        pass

    return matches
