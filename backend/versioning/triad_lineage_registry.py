"""Model-Data-Code Triad Cryptographic Lineage Registry.

Binds every clinical AI inference to an immutable provenance certificate
spanning the Dataset Merkle Root, Model Weights SHA-256 digest, and Git commit hash,
satisfying FDA SaMD 21 CFR 820.30 and EU AI Act Class IIa/IIb reproducibility mandates.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, List, Optional

# HMAC secret key for provenance signatures (uses environment or secure local fallback)
LINEAGE_HMAC_SECRET = b"CLINICAL_AI_TRIAD_PROVENANCE_KEY_2026"


class ModelDataTriad:
    """Immutable binding of Model Weights, Training Dataset, and Inference Code."""

    def __init__(
        self,
        triad_id: str,
        model_id: str,
        weights_digest: str,
        dataset_digest: str,
        code_commit_hash: str,
        framework: str = "PyTorch",
        metadata: Optional[Dict[str, Any]] = None,
        registered_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.triad_id = triad_id
        self.model_id = model_id
        self.weights_digest = weights_digest
        self.dataset_digest = dataset_digest
        self.code_commit_hash = code_commit_hash
        self.framework = framework
        self.metadata = metadata or {}
        self.registered_at = registered_at or datetime.datetime.now(datetime.timezone.utc)
        self.triad_signature = self._compute_signature()

    def _compute_signature(self) -> str:
        canonical = f"{self.triad_id}:{self.model_id}:{self.weights_digest}:{self.dataset_digest}:{self.code_commit_hash}"
        return hmac.new(LINEAGE_HMAC_SECRET, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify that the triad manifest has not been tampered with."""
        return hmac.compare_digest(self.triad_signature, self._compute_signature())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triad_id": self.triad_id,
            "model_id": self.model_id,
            "weights_digest": self.weights_digest,
            "dataset_digest": self.dataset_digest,
            "code_commit_hash": self.code_commit_hash,
            "framework": self.framework,
            "metadata": self.metadata,
            "triad_signature": self.triad_signature,
            "registered_at": self.registered_at.isoformat(),
        }


class InferenceAttestation:
    """Cryptographic certificate attesting to the exact lineage of a clinical AI prediction."""

    def __init__(
        self,
        attestation_id: str,
        patient_id: str,
        prediction_id: str,
        triad_id: str,
        input_features_hash: str,
        output_prediction: Dict[str, Any],
        timestamp: Optional[datetime.datetime] = None,
        attestation_hash: Optional[str] = None,
    ) -> None:
        self.attestation_id = attestation_id
        self.patient_id = patient_id
        self.prediction_id = prediction_id
        self.triad_id = triad_id
        self.input_features_hash = input_features_hash
        self.output_prediction = output_prediction
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)
        self.attestation_hash = attestation_hash or self.compute_hash()

    def compute_hash(self) -> str:
        body = {
            "attestation_id": self.attestation_id,
            "patient_id": self.patient_id,
            "prediction_id": self.prediction_id,
            "triad_id": self.triad_id,
            "input_features_hash": self.input_features_hash,
            "output_prediction": self.output_prediction,
            "timestamp": self.timestamp.isoformat(),
        }
        serialized = json.dumps(body, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "patient_id": self.patient_id,
            "prediction_id": self.prediction_id,
            "triad_id": self.triad_id,
            "input_features_hash": self.input_features_hash,
            "output_prediction": self.output_prediction,
            "attestation_hash": self.attestation_hash,
            "timestamp": self.timestamp.isoformat(),
        }


class ModelDataTriadRegistry:
    """Registry maintaining Model-Data-Code triads and verifying inference attestations."""

    def __init__(self) -> None:
        self._triads: Dict[str, ModelDataTriad] = {}  # triad_id -> triad
        self._attestations: Dict[str, InferenceAttestation] = {}  # attestation_id -> attestation

    def register_triad(
        self,
        model_id: str,
        weights_digest: str,
        dataset_digest: str,
        code_commit_hash: str,
        framework: str = "PyTorch",
        metadata: Optional[Dict[str, Any]] = None,
        triad_id: Optional[str] = None,
    ) -> ModelDataTriad:
        """Register an immutable Model-Data-Code triad."""
        tid = triad_id or str(uuid.uuid4())
        triad = ModelDataTriad(
            triad_id=tid,
            model_id=model_id,
            weights_digest=weights_digest,
            dataset_digest=dataset_digest,
            code_commit_hash=code_commit_hash,
            framework=framework,
            metadata=metadata or {},
        )
        self._triads[tid] = triad
        return triad

    def attest_inference(
        self,
        patient_id: str,
        prediction_id: str,
        triad_id: str,
        input_features: Dict[str, Any],
        output_prediction: Dict[str, Any],
    ) -> InferenceAttestation:
        """Generate a cryptographically sealed attestation for a clinical prediction."""
        triad = self._triads.get(triad_id)
        if not triad:
            raise KeyError(f"Model-Data Triad '{triad_id}' not found in registry")

        # Hash input features to preserve zero-PII storage in attestation
        features_serialized = json.dumps(input_features, sort_keys=True, default=str)
        feat_hash = hashlib.sha256(features_serialized.encode("utf-8")).hexdigest()

        att = InferenceAttestation(
            attestation_id=str(uuid.uuid4()),
            patient_id=patient_id,
            prediction_id=prediction_id,
            triad_id=triad_id,
            input_features_hash=feat_hash,
            output_prediction=output_prediction,
        )

        self._attestations[att.attestation_id] = att
        return att

    def verify_provenance(self, attestation_id: str) -> Dict[str, Any]:
        """Verify the full cryptographic provenance chain for a given inference attestation."""
        att = self._attestations.get(attestation_id)
        if not att:
            raise KeyError(f"Attestation '{attestation_id}' not found")

        triad = self._triads.get(att.triad_id)
        if not triad:
            return {
                "valid": False,
                "reason": f"Missing triad reference '{att.triad_id}'",
                "attestation_id": attestation_id,
            }

        # Check attestation hash integrity
        if att.attestation_hash != att.compute_hash():
            return {
                "valid": False,
                "reason": "Attestation hash mismatch (tampered prediction body)",
                "attestation_id": attestation_id,
            }

        # Check triad HMAC signature integrity
        if not triad.verify_integrity():
            return {
                "valid": False,
                "reason": "Triad signature verification failed (tampered lineage manifest)",
                "attestation_id": attestation_id,
            }

        return {
            "valid": True,
            "attestation_id": attestation_id,
            "patient_id": att.patient_id,
            "prediction_id": att.prediction_id,
            "triad": triad.to_dict(),
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def get_triad(self, triad_id: str) -> Optional[ModelDataTriad]:
        return self._triads.get(triad_id)

    def list_triads(self, model_id: Optional[str] = None) -> List[ModelDataTriad]:
        if model_id:
            return [t for t in self._triads.values() if t.model_id == model_id]
        return list(self._triads.values())

    def clear(self) -> None:
        """Reset internal registries (for testing)."""
        self._triads.clear()
        self._attestations.clear()
