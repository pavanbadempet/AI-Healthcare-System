use axum::{
    body::{Body, Bytes},
    extract::{Request, State},
    http::{uri::Uri, HeaderMap, Method, StatusCode},
    response::Response,
};
use reqwest::Client;
use std::net::SocketAddr;
use dotenvy::dotenv;
use std::env;
use std::sync::{Arc, Mutex};
use sysinfo::System;

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

#[derive(Clone)]
pub struct AppState {
    pub http_client: Client,
    pub python_backend_url: String,
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

    let db_url = env::var("DATABASE_URL").unwrap_or_else(|_| "sqlite://healthcare.db".to_string());
    let secret_key = env::var("SECRET_KEY").unwrap_or_else(|_| "test_secret_key_for_local_tests_only".to_string());

    // Connect to database (SQLite WAL mode or PostgreSQL) and auto-initialize schema
    let pool = db::DbPool::new(&db_url).await.unwrap_or_else(|err| {
        println!("Warning: Failed to connect to DB ({:?}). Falling back to lazy in-memory SQLite pool.", err);
        db::DbPool::connect_lazy("sqlite::memory:").expect("Failed to create fallback pool")
    });

    // Initialize System metric collector with a default system refresh all configuration
    let sys = System::new_all();

    // Compile-time SOTA IPC configuration: Unix Domain Sockets on Unix, tuned TCP loopback on Windows
    #[cfg(unix)]
    let (http_client, python_backend_url) = {
        let client = Client::builder()
            .unix_socket("/tmp/healthcare.sock")
            .tcp_nodelay(true)
            .pool_max_idle_per_host(100)
            .build()
            .expect("Failed to build Unix Domain Socket HTTP client");
        (client, "http://uds".to_string())
    };

    #[cfg(not(unix))]
    let (http_client, python_backend_url) = {
        let client = Client::builder()
            .tcp_nodelay(true)
            .pool_max_idle_per_host(100)
            .pool_idle_timeout(std::time::Duration::from_secs(90))
            .tcp_keepalive(Some(std::time::Duration::from_secs(60)))
            .build()
            .expect("Failed to build tuned TCP loopback HTTP client");
        let backend_url = env::var("PYTHON_BACKEND_URL").unwrap_or_else(|_| "http://127.0.0.1:8000".to_string());
        (client, backend_url)
    };

    let vector_store_state = vector_store::VectorStoreState::default();

    let inference_manager = Arc::new(
        ml::InferenceManager::new()
            .or_else(|_| ml::InferenceManager::from_dir("../backend"))
            .or_else(|_| ml::InferenceManager::from_dir("backend"))
            .unwrap_or_else(|err| {
                println!("Warning: ONNX model loading error ({:?}). Retrying with default env.", err);
                ml::InferenceManager::new().expect("Failed to initialize InferenceManager")
            })
    );

    let state = AppState {
        http_client,
        python_backend_url,
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
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8001);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Gateway listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

pub async fn proxy_handler_fallback(
    State(state): State<AppState>,
    req: Request,
) -> Result<Response, StatusCode> {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let headers = req.headers().clone();
    
    let path = uri.path();
    let path_query = uri
        .path_and_query()
        .map(|v| v.as_str())
        .unwrap_or(path);

    let proxy_uri = format!("{}{}", state.python_backend_url, path_query);

    let correlation_id = headers
        .get("X-Correlation-ID")
        .or_else(|| headers.get("x-correlation-id"))
        .or_else(|| headers.get("X-Request-ID"))
        .or_else(|| headers.get("x-request-id"))
        .and_then(|v| v.to_str().ok().map(|s| s.to_string()))
        .unwrap_or_else(|| {
            use std::time::{SystemTime, UNIX_EPOCH};
            let start = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0);
            format!("corr-{}", start)
        });

    println!("[{}] Proxying request to: {}", correlation_id, proxy_uri);

    let mut reqwest_req = state.http_client.request(method, proxy_uri);
    
    for (name, value) in headers.iter() {
        if name.as_str().to_lowercase() == "host" {
            continue;
        }
        reqwest_req = reqwest_req.header(name, value);
    }
    
    // Inject Correlation/Request ID into the outgoing request
    reqwest_req = reqwest_req.header("X-Correlation-ID", &correlation_id);
    reqwest_req = reqwest_req.header("X-Request-ID", &correlation_id);

    // Stream the request body instead of collecting it in memory!
    let body_stream = req.into_body().into_data_stream();
    let body = reqwest::Body::wrap_stream(body_stream);

    let res = reqwest_req
        .body(body)
        .send()
        .await
        .map_err(|_| StatusCode::BAD_GATEWAY)?;

    let mut axum_res = axum::http::Response::builder().status(res.status());
    
    for (name, value) in res.headers().iter() {
        axum_res = axum_res.header(name, value);
    }
    
    // Inject Correlation/Request ID into the response headers
    axum_res = axum_res.header("X-Correlation-ID", &correlation_id);
    axum_res = axum_res.header("X-Request-ID", &correlation_id);

    let stream = res.bytes_stream();
    let body = Body::from_stream(stream);

    let response = axum_res
        .body(body)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(response)
}

/// Core function to execute the proxy request with a buffered body
pub async fn execute_proxy(
    state: &AppState,
    method: Method,
    original_uri: Uri,
    headers: HeaderMap,
    body_bytes: Bytes,
) -> Result<Response, StatusCode> {
    let path = original_uri.path();
    let path_query = original_uri
        .path_and_query()
        .map(|v| v.as_str())
        .unwrap_or(path);

    let uri = format!("{}{}", state.python_backend_url, path_query);

    let correlation_id = headers
        .get("X-Correlation-ID")
        .or_else(|| headers.get("x-correlation-id"))
        .or_else(|| headers.get("X-Request-ID"))
        .or_else(|| headers.get("x-request-id"))
        .and_then(|v| v.to_str().ok().map(|s| s.to_string()))
        .unwrap_or_else(|| {
            use std::time::{SystemTime, UNIX_EPOCH};
            let start = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0);
            format!("corr-{}", start)
        });

    println!("[{}] Proxying request to: {}", correlation_id, uri);

    let mut reqwest_req = state.http_client.request(method, uri);
    
    for (name, value) in headers.iter() {
        if name.as_str().to_lowercase() == "host" {
            continue;
        }
        reqwest_req = reqwest_req.header(name, value);
    }
    
    // Inject Correlation/Request ID into the outgoing request
    reqwest_req = reqwest_req.header("X-Correlation-ID", &correlation_id);
    reqwest_req = reqwest_req.header("X-Request-ID", &correlation_id);

    let res = reqwest_req
        .body(body_bytes)
        .send()
        .await
        .map_err(|_| StatusCode::BAD_GATEWAY)?;

    let mut axum_res = axum::http::Response::builder().status(res.status());
    
    for (name, value) in res.headers().iter() {
        axum_res = axum_res.header(name, value);
    }
    
    // Inject Correlation/Request ID into the response headers
    axum_res = axum_res.header("X-Correlation-ID", &correlation_id);
    axum_res = axum_res.header("X-Request-ID", &correlation_id);

    let stream = res.bytes_stream();
    let body = Body::from_stream(stream);

    let response = axum_res
        .body(body)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(response)
}
