use reqwest::Client;
use std::net::SocketAddr;
use dotenvy::dotenv;
use std::env;
use std::sync::{Arc, Mutex};
use sysinfo::System;

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod auth;
mod appointments;
mod telehealth;
mod claims;
mod telemetry;
mod codec;
mod fhir;
mod tee_enclave;
mod vector_store;
mod interop_grpc;
mod clinical_calculator;
mod phi_redactor;
mod ecg_dsp;
mod dicom_slicer;
mod auth_crypto;
mod billing_audit;
mod federated_aggregator;
pub mod db;
pub mod models;
pub mod ml;
pub mod routes;
pub mod invariant_gate;
pub mod dialectical_consensus;

#[derive(Clone)]
pub struct AppState {
    pub http_client: Client,
    pub db_pool: db::DbPool,
    pub secret_key: String,
    pub sysinfo: Arc<Mutex<System>>,
    pub vector_store: vector_store::VectorStoreState,
    pub inference_manager: Arc<ml::InferenceManager>,
}

#[tokio::main]
async fn main() {
    // Load .env file if present
    let _ = dotenv();
    
    println!("Starting Rust API Gateway...");

    let db_url = env::var("DATABASE_URL")
        .or_else(|_| env::var("NEON_DATABASE_URL"))
        .or_else(|_| env::var("POSTGRES_URL"))
        .or_else(|_| env::var("POSTGRESQL_URL"))
        .unwrap_or_else(|_| "sqlite://healthcare.db".to_string());
    let secret_key = env::var("SECRET_KEY").unwrap_or_else(|_| "test_secret_key_for_local_tests_only".to_string());

    // Connect to database (SQLite WAL mode or PostgreSQL) and auto-initialize schema
    let pool = match db::DbPool::new(&db_url).await {
        Ok(p) => p,
        Err(err) => {
            eprintln!("Warning: Failed to connect to DB at {} ({:?}). Initializing in-memory fallback pool with schema.", db_url, err);
            db::DbPool::new("sqlite::memory:")
                .await
                .expect("Failed to create in-memory SQLite fallback pool with schema")
        }
    };

    // Initialize System metric collector with a default system refresh all configuration
    let sys = System::new_all();

    // Standard outbound HTTP client for external integrations (zero Python IPC coupling)
    let http_client = Client::builder()
        .tcp_nodelay(true)
        .pool_max_idle_per_host(100)
        .pool_idle_timeout(std::time::Duration::from_secs(90))
        .tcp_keepalive(Some(std::time::Duration::from_secs(60)))
        .build()
        .unwrap_or_else(|_| Client::new());

    let vector_store_state = vector_store::VectorStoreState::default();

    let inference_manager = Arc::new(
        ml::InferenceManager::new()
            .or_else(|_| ml::InferenceManager::from_dir("backend"))
            .or_else(|_| ml::InferenceManager::from_dir("../backend"))
            .or_else(|_| ml::InferenceManager::from_dir("."))
            .unwrap_or_else(|err| {
                println!("Warning: ONNX model loading error ({:?}). Creating fallback manager.", err);
                ml::InferenceManager::from_dir("backend")
                    .or_else(|_| ml::InferenceManager::new())
                    .unwrap_or_else(|_| {
                        panic!("Failed to initialize InferenceManager: {:?}", err);
                    })
            })
    );

    let state = AppState {
        http_client,
        db_pool: pool,
        secret_key,
        sysinfo: Arc::new(Mutex::new(sys)),
        vector_store: vector_store_state.clone(),
        inference_manager,
    };

    // Spin up gRPC Server on port 50051
    tokio::spawn(async {
        if let Err(e) = interop_grpc::start_grpc_server(50051).await {
            eprintln!("gRPC Server Error: {:?}", e);
        }
    });

    let app = routes::build_app_router(state);

    let port: u16 = env::var("PORT")
        .or_else(|_| env::var("RUST_PORT"))
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8000);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Gateway listening on http://{}", addr);

    let listener = {
        let mut retries = 5;
        loop {
            match tokio::net::TcpListener::bind(&addr).await {
                Ok(l) => break l,
                Err(e) if retries > 0 => {
                    eprintln!("Warning: Failed to bind to {} ({:?}), retrying in 1s...", addr, e);
                    tokio::time::sleep(std::time::Duration::from_secs(1)).await;
                    retries -= 1;
                }
                Err(e) => panic!("Failed to bind to {}: {:?}", addr, e),
            }
        }
    };
    axum::serve(listener, app).await.unwrap();
}
