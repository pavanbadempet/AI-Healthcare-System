import pytest
from backend.tee_enclave import ConfidentialEnclave, EnclaveAttestationError

def test_enclave_attestation_success():
    enclave = ConfidentialEnclave(expected_hash="2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae")
    # Hash for "foo"
    payload = b"foo"
    assert enclave.attest(payload) is True

def test_enclave_attestation_failure():
    enclave = ConfidentialEnclave(expected_hash="invalid_hash")
    with pytest.raises(EnclaveAttestationError):
        enclave.attest(b"foo")

def test_enclave_wipes_memory():
    enclave = ConfidentialEnclave()
    enclave._attested = True # Bypass hash check for this test
    
    sensitive_data = bytearray(b"SENSITIVE_PATIENT_DATA")
    
    def my_sensitive_func(data):
        return data.decode("utf-8")
        
    result = enclave.execute(my_sensitive_func, sensitive_data)
    
    assert result == "SENSITIVE_PATIENT_DATA"
    # Because of the memory wipe, the bytearray should now be null bytes
    assert sensitive_data == bytearray(b"\x00" * 22)

@pytest.mark.asyncio
async def test_enclave_async_wipes_memory():
    enclave = ConfidentialEnclave()
    enclave._attested = True # Bypass hash check for this test
    
    sensitive_data = bytearray(b"SENSITIVE_PATIENT_DATA")
    
    async def my_sensitive_func(data):
        return data.decode("utf-8")
        
    result = await enclave.execute_async(my_sensitive_func, sensitive_data)
    
    assert result == "SENSITIVE_PATIENT_DATA"
    # Because of the memory wipe, the bytearray should now be null bytes
    assert sensitive_data == bytearray(b"\x00" * 22)
