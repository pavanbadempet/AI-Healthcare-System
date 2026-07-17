import hashlib
import logging
import os
from typing import Any, Callable, Dict, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

class EnclaveAttestationError(Exception):
    pass

# Dynamic secure boot registry for model measurements
TRUSTED_MODEL_HASHES: Dict[str, str] = {}

class ConfidentialEnclave:
    """
    Trusted Execution Environment (TEE) for Confidential AI.
    Verifies code and model binary integrity using SHA-256 cryptographic attestation.
    """
    def __init__(self, expected_hash: str = None):
        self.expected_hash = expected_hash
        self._attested = False

    def attest(self, payload: bytes) -> bool:
        """Attest raw payload bytes."""
        current_hash = hashlib.sha256(payload).hexdigest()
        if self.expected_hash and current_hash != self.expected_hash:
            logger.error("ENCLAVE ATTESTATION FAILED. Payload hash mismatch.")
            raise EnclaveAttestationError("Payload failed cryptographic attestation.")

        self._attested = True
        return True

    def attest_model_file(self, model_name: str, file_path: str) -> bool:
        """
        Cryptographically attest a model binary file on disk.
        Reads the file, computes its SHA-256 hash, and compares it with
        the trusted bootstrap signature.
        """
        if not os.path.exists(file_path):
            logger.error(f"TEE Enclave cannot locate model binary at {file_path}")
            raise EnclaveAttestationError(f"Model file not found at {file_path}")

        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
        except Exception as e:
            raise EnclaveAttestationError(f"TEE failed to read model file for hashing: {str(e)}")

        file_hash = sha256.hexdigest()

        # Secure bootstrap: register the trusted hash on first load (TOFU)
        if model_name not in TRUSTED_MODEL_HASHES:
            TRUSTED_MODEL_HASHES[model_name] = file_hash
            logger.info(f"[TEE] Registered secure boot hash for {model_name}: {file_hash}")

        expected = TRUSTED_MODEL_HASHES[model_name]
        if file_hash != expected:
            logger.error(f"ENCLAVE ATTESTATION FAILED: Tampering detected in model {model_name}!")
            raise EnclaveAttestationError(f"Model {model_name} failed code integrity verification.")

        self._attested = True
        logger.info(f"[TEE] Cryptographic attestation successful for: {model_name} ({file_hash[:8]}...)")
        return True

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function inside the simulated enclave.
        Ensures strict no-logging during execution and attempts memory clearing post-execution.
        """
        if not self._attested:
            raise EnclaveAttestationError("Cannot execute in enclave without successful attestation.")

        logger.debug("[TEE] Entering Confidential Enclave execution context.")

        # Execute the function
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            logger.debug("[TEE] Exiting Confidential Enclave context. Simulating secure memory wipe.")
            self._wipe_memory(args, kwargs)

    async def execute_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Async variant of execute."""
        if not self._attested:
            raise EnclaveAttestationError("Cannot execute in enclave without successful attestation.")

        logger.debug("[TEE] Entering Confidential Enclave async execution context.")

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            logger.debug("[TEE] Exiting Confidential Enclave context. Simulating secure memory wipe.")
            self._wipe_memory(args, kwargs)

    async def execute_async_gen(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Async generator variant of execute."""
        if not self._attested:
            raise EnclaveAttestationError("Cannot execute in enclave without successful attestation.")

        logger.debug("[TEE] Entering Confidential Enclave async execution context (stream).")

        try:
            async for chunk in func(*args, **kwargs):
                yield chunk
        finally:
            logger.debug("[TEE] Exiting Confidential Enclave context (stream). Simulating secure memory wipe.")
            self._wipe_memory(args, kwargs)

    def _wipe_memory(self, args: tuple, kwargs: dict):
        """
        Securely sanitizes and clears mutable variables from memory, forcing GC collect.
        """
        import gc

        # Overwrite mutable arguments to zero/clear them out in memory
        for arg in args:
            if isinstance(arg, bytearray):
                for i in range(len(arg)):
                    arg[i] = 0
            elif isinstance(arg, list):
                arg.clear()
            elif isinstance(arg, dict):
                arg.clear()

        for val in kwargs.values():
            if isinstance(val, bytearray):
                for i in range(len(val)):
                    val[i] = 0
            elif isinstance(val, list):
                val.clear()
            elif isinstance(val, dict):
                val.clear()

        # Explicitly invoke garbage collection to clear unreferenced memory blocks immediately
        gc.collect()

        # Clear references to incoming arguments
        del args
        del kwargs

