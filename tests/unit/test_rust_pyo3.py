import os
import shutil
import sys

def test_rust_pyo3():
    if sys.platform == "win32":
        src_name = "rust_gateway_ffi.dll"
        dest_name = "rust_gateway_ffi.pyd"
    elif sys.platform == "darwin":
        src_name = "librust_gateway_ffi.dylib"
        dest_name = "rust_gateway_ffi.so"
    else:
        src_name = "librust_gateway_ffi.so"
        dest_name = "rust_gateway_ffi.so"

    # Resolve paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(base_dir, "..", "..", "rust_gateway", "target", "debug", src_name)
    src_path = os.path.abspath(src_path)

    if not os.path.exists(src_path):
        return

    # Copy binary to current folder with .pyd/.so name so python can import it
    dest_path = os.path.join(base_dir, dest_name)
    shutil.copyfile(src_path, dest_path)

    # Add tests directory to path
    sys.path.insert(0, base_dir)

    try:
        # NATIVE IMPORT OF THE RUST BINARY
        import rust_gateway_ffi

        # Test native validation
        valid_patient = '{"resourceType": "Patient", "id": "pat123", "name": [{"text": "Alice"}]}'
        assert rust_gateway_ffi.validate_fhir_patient_py(valid_patient) is True

        invalid_patient = '{"resourceType": "Patient", "id": "pat123", "active": true}'
        assert rust_gateway_ffi.validate_fhir_patient_py(invalid_patient) is False

    finally:
        # Clean up copied file
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
