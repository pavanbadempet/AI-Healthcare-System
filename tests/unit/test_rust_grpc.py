import os
import subprocess
import time
import sys
import grpc

# Add tests/unit to path to import generated interop_pb2
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

import interop_pb2

def test_rust_grpc_server():
    # Find compiled binary path
    binary_name = "rust_gateway.exe" if sys.platform == "win32" else "rust_gateway"
    binary_path = os.path.join(base_dir, "..", "..", "rust_gateway", "target", "debug", binary_name)
    binary_path = os.path.abspath(binary_path)

    # Compile the binary first to ensure it's up to date
    compile_cmd = ["cargo", "build", "--bin", "rust_gateway"]
    env = os.environ.copy()
    if sys.platform == "win32":
        env["PATH"] += ";C:\\Users\\pavan\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Google.Protobuf_Microsoft.Winget.Source_8wekyb3d8bbwe\\bin"
    
    # We do a build to ensure the binary is compiled with gRPC support
    rust_gw_dir = os.path.join(base_dir, "..", "..", "rust_gateway")
    subprocess.run(compile_cmd, cwd=rust_gw_dir, env=env, check=True)

    # Start the Rust gateway server in a background subprocess
    proc = subprocess.Popen(
        [binary_path],
        cwd=rust_gw_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for the gRPC server to start listening
    time.sleep(3.0)

    try:
        # Create insecure channel to our tonic gRPC server
        channel = grpc.insecure_channel('127.0.0.1:50051')

        # Define unary methods
        validate_fhir = channel.unary_unary(
            '/interop.InteropService/ValidateFhir',
            request_serializer=interop_pb2.FhirRequest.SerializeToString,
            response_deserializer=interop_pb2.FhirResponse.FromString,
        )

        attest_enclave = channel.unary_unary(
            '/interop.InteropService/AttestEnclave',
            request_serializer=interop_pb2.EnclaveRequest.SerializeToString,
            response_deserializer=interop_pb2.EnclaveResponse.FromString,
        )

        # 1. Test FHIR validation gRPC Call
        valid_patient_json = '{"resourceType": "Patient", "id": "pat789", "name": [{"text": "Charlie"}]}'
        req1 = interop_pb2.FhirRequest(json_payload=valid_patient_json)
        resp1 = validate_fhir(req1)
        assert resp1.valid is True
        assert resp1.resource_type == "Patient"

        invalid_patient_json = '{"resourceType": "Patient", "id": "pat789", "active": true}'
        req2 = interop_pb2.FhirRequest(json_payload=invalid_patient_json)
        resp2 = validate_fhir(req2)
        assert resp2.valid is False

        # 2. Test TEE Enclave attestation gRPC Call
        req3 = interop_pb2.EnclaveRequest(model_name="diabetes_v1", model_bytes=b"model-weights-binary-data")
        resp3 = attest_enclave(req3)
        assert resp3.attested is True

    finally:
        # Terminate the server subprocess
        proc.terminate()
        proc.wait()
