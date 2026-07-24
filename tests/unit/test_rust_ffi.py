import ctypes
import os
import sys


def test_rust_ffi():
    if sys.platform == "win32":
        lib_name = "rust_gateway_ffi.dll"
    elif sys.platform == "darwin":
        lib_name = "librust_gateway_ffi.dylib"
    else:
        lib_name = "librust_gateway_ffi.so"

    # Resolve absolute path to target build directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lib_path = os.path.join(base_dir, "..", "..", "rust_gateway", "target", "debug", lib_name)
    lib_path = os.path.abspath(lib_path)

    if not os.path.exists(lib_path):
        return

    # Load library via ctypes
    lib = ctypes.CDLL(lib_path)

    # Bind signatures
    lib.validate_fhir_patient_ffi.argtypes = [ctypes.c_char_p]
    lib.validate_fhir_patient_ffi.restype = ctypes.c_bool

    # Test valid patient
    valid_patient = b'{"resourceType": "Patient", "id": "pat123", "name": [{"text": "Alice"}]}'
    assert lib.validate_fhir_patient_ffi(valid_patient) is True

    # Test invalid patient (not a placeholder because of 'active' key, but missing name)
    invalid_patient = b'{"resourceType": "Patient", "id": "pat123", "active": true}'
    assert lib.validate_fhir_patient_ffi(invalid_patient) is False
