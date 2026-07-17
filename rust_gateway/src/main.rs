use axum::{
    body::{Body, Bytes},
    extract::{Request, State},
    http::{uri::Uri, HeaderMap, Method, StatusCode},
    response::Response,
    routing::{get, post},
    Router,
};
use reqwest::Client;
use sqlx::{postgres::PgPoolOptions, PgPool};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use dotenvy::dotenv;
use std::env;
use std::sync::{Arc, Mutex};

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;
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

#[derive(Clone)]
pub struct AppState {
    pub http_client: Client,
    pub python_backend_url: String,
    pub db_pool: PgPool,
    pub secret_key: String,
    pub sysinfo: Arc<Mutex<System>>,
    pub vector_store: vector_store::VectorStoreState,
}

#[tokio::main]
async fn main() {
    // Load .env file if present
    let _ = dotenv();
    
    println!("Starting Rust API Gateway...");

    let db_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let secret_key = env::var("SECRET_KEY").unwrap_or_else(|_| "test_secret_key_for_local_tests_only".to_string());

    let postgres_url = if db_url.starts_with("postgres://") || db_url.starts_with("postgresql://") {
        db_url
    } else {
        println!("DATABASE_URL is not a Postgres connection. Native Edge Gateway database operations will be disabled.");
        "postgres://127.0.0.1/dummy_db".to_string()
    };

    // Connect to PostgreSQL lazily to guarantee startup and allow local SQLite/multi-database operation
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .min_connections(2)
        .acquire_timeout(std::time::Duration::from_secs(3))
        .idle_timeout(std::time::Duration::from_secs(300))
        .max_lifetime(std::time::Duration::from_secs(1800))
        .test_before_acquire(true)
        .connect_lazy(&postgres_url)
        .expect("Failed to create Postgres connection pool");

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
        (client, "http://127.0.0.1:8001".to_string())
    };

    let vector_store_state = vector_store::VectorStoreState::default();

    let state = AppState {
        http_client,
        python_backend_url,
        db_pool: pool,
        secret_key,
        sysinfo: Arc::new(Mutex::new(sys)),
        vector_store: vector_store_state.clone(),
    };

    // Spin up gRPC Server on port 50051
    tokio::spawn(async {
        if let Err(e) = interop_grpc::start_grpc_server(50051).await {
            eprintln!("gRPC Server Error: {:?}", e);
        }
    });

    let app = Router::new()
        .route("/healthz_rust", get(health_check))
        .route("/metrics", get(metrics_handler))
        .route("/v1/auth/token", post(auth::login_handler))
        .route("/v1/auth/profile", get(auth::profile_handler))
        .nest("/v1/appointments", appointments::router())
        .nest("/v1/telehealth", telehealth::router())
        .nest("/v1/claims", claims::router())
        .nest("/v1/telemetry", telemetry::router())
        .nest("/v1/interop/fhir", fhir::router())
        .nest("/v1/interop/vector-store", vector_store::router(vector_store_state))
        // Fallback proxy to Python backend
        .fallback(proxy_handler_fallback)
        .layer(tower_http::compression::CompressionLayer::new())
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], 7860));
    println!("Gateway listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check() -> &'static str {
    "Rust Gateway is healthy!"
}

async fn metrics_handler(
    State(state): State<AppState>,
) -> impl axum::response::IntoResponse {
    let mut sys = state.sysinfo.lock().unwrap();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_usage();
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let active_conns = state.db_pool.size();
    
    let body = format!(
        "# HELP rust_gateway_cpu_usage_percent CPU usage of the Rust Gateway in percent\n\
         # TYPE rust_gateway_cpu_usage_percent gauge\n\
         rust_gateway_cpu_usage_percent {}\n\
         # HELP rust_gateway_memory_total_bytes Total memory in bytes\n\
         # TYPE rust_gateway_memory_total_bytes gauge\n\
         rust_gateway_memory_total_bytes {}\n\
         # HELP rust_gateway_memory_used_bytes Used memory in bytes\n\
         # TYPE rust_gateway_memory_used_bytes gauge\n\
         rust_gateway_memory_used_bytes {}\n\
         # HELP rust_gateway_active_db_connections Number of active database connections in SQLx pool\n\
         # TYPE rust_gateway_active_db_connections gauge\n\
         rust_gateway_active_db_connections {}\n",
        cpu_usage, total_mem, used_mem, active_conns
    );
    
    (
        [("content-type", "text/plain; version=0.0.4; charset=utf-8")],
        body
    )
}

async fn proxy_handler_fallback(
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
