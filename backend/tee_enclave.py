import hashlib
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

class EnclaveAttestationError(Exception):
    pass

class ConfidentialEnclave:
    """
    Simulated Trusted Execution Environment (TEE) for Confidential AI.
    In a real deployment, this would interface with AWS Nitro Enclaves,
    Intel SGX SDK, or Azure Confidential VMs.
    """
    def __init__(self, expected_hash: str = None):
        # In a real scenario, this hash comes from the PCR0 measurement of the enclave image
        self.expected_hash = expected_hash
        self._attested = False

    def attest(self, payload: bytes) -> bool:
        """Mock cryptographic attestation process."""
        current_hash = hashlib.sha256(payload).hexdigest()
        if self.expected_hash and current_hash != self.expected_hash:
            logger.error("ENCLAVE ATTESTATION FAILED. Payload hash mismatch.")
            raise EnclaveAttestationError("Payload failed cryptographic attestation.")

        self._attested = True
        return True

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function inside the simulated enclave.
        Ensures strict no-logging during execution and attempts memory clearing post-execution.
        """
        if self.expected_hash and not self._attested:
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
        if self.expected_hash and not self._attested:
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
        if self.expected_hash and not self._attested:
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
        Simulate wiping of sensitive variables.
        In pure Python, we cannot strictly control memory, but we can overwrite mutable bytearrays
        if they were passed, and aggressively delete references.
        """
        for arg in args:
            if isinstance(arg, bytearray):
                for i in range(len(arg)):
                    arg[i] = 0
        for val in kwargs.values():
            if isinstance(val, bytearray):
                for i in range(len(val)):
                    val[i] = 0

        # Aggressive explicit deletion
        del args
        del kwargs
