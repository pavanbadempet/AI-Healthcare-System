use tonic::{transport::Server, Request, Response, Status};
use serde_json::Value;

pub mod interop {
    tonic::include_proto!("interop");
}

use interop::interop_service_server::{InteropService, InteropServiceServer};
use interop::{
    FhirRequest, FhirResponse, EnclaveRequest, EnclaveResponse,
    VectorSearchRequest, VectorSearchResponse
};

use crate::fhir;
use crate::tee_enclave;

#[derive(Default)]
pub struct MyInteropService {}

#[tonic::async_trait]
impl InteropService for MyInteropService {
    async fn validate_fhir(
        &self,
        request: Request<FhirRequest>,
    ) -> Result<Response<FhirResponse>, Status> {
        let req = request.into_inner();
        let payload: Value = serde_json::from_str(&req.json_payload)
            .map_err(|e| Status::invalid_argument(format!("Invalid JSON: {}", e)))?;
        
        let res = fhir::validate_fhir_resource_sync(&payload);
        Ok(Response::new(FhirResponse {
            valid: res.valid,
            resource_type: res.resource_type,
            errors: res.errors,
        }))
    }

    async fn attest_enclave(
        &self,
        request: Request<EnclaveRequest>,
    ) -> Result<Response<EnclaveResponse>, Status> {
        let req = request.into_inner();
        let mut enclave = tee_enclave::SecureConfidentialEnclave::new(None);
        let attested = enclave.attest_model(&req.model_name, &req.model_bytes);
        Ok(Response::new(EnclaveResponse { attested }))
    }

    async fn search_vectors(
        &self,
        _request: Request<VectorSearchRequest>,
    ) -> Result<Response<VectorSearchResponse>, Status> {
        Ok(Response::new(VectorSearchResponse {
            records: vec![]
        }))
    }
}

pub async fn start_grpc_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let addr = format!("127.0.0.1:{}", port).parse()?;
    let service = MyInteropService::default();

    println!("Starting native gRPC Interop Server on Address: {}", addr);

    Server::builder()
        .add_service(InteropServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
