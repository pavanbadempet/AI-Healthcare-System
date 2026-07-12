use axum::{
    body::{Body, Bytes},
    extract::{Request, State},
    http::{uri::Uri, StatusCode, Method, HeaderMap},
    response::{IntoResponse, Response},
    routing::{any, post, get},
    Json, Router,
};
use http_body_util::BodyExt;
use reqwest::Client;
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use dotenvy::dotenv;
use std::env;

mod auth;

#[derive(Clone)]
pub struct AppState {
    pub http_client: Client,
    pub python_backend_url: String,
    pub db_pool: SqlitePool,
    pub secret_key: String,
}

#[tokio::main]
async fn main() {
    // Load .env file if present
    let _ = dotenv();
    
    println!("Starting Rust API Gateway...");

    let db_url = env::var("DATABASE_URL").unwrap_or_else(|_| "sqlite://../healthcare.db".to_string());
    let secret_key = env::var("SECRET_KEY").unwrap_or_else(|_| "test_secret_key_for_local_tests_only".to_string());

    // Connect to SQLite with WAL mode enabled to support concurrent readers/writers
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&db_url)
        .await
        .expect("Failed to create SQLite connection pool");

    let state = AppState {
        http_client: Client::new(),
        python_backend_url: "http://127.0.0.1:8001".to_string(), // Python server port
        db_pool: pool,
        secret_key,
    };

    let app = Router::new()
        .route("/healthz_rust", get(health_check))
        .route("/v1/auth/token", post(auth::login_handler))
        .route("/v1/auth/profile", get(auth::profile_handler))
        // Fallback proxy to Python backend
        .fallback(any(proxy_handler_fallback))
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

/// A generic Axum handler for the fallback proxy
async fn proxy_handler_fallback(
    State(state): State<AppState>,
    req: Request,
) -> Result<Response, StatusCode> {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let headers = req.headers().clone();
    
    // Collect body bytes
    let body_bytes = req.into_body().collect().await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.to_bytes();
    
    execute_proxy(&state, method, uri, headers, body_bytes).await
}

/// Core function to execute the proxy request
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

    println!("Proxying request to: {}", uri);

    let mut reqwest_req = state.http_client.request(method, uri);
    
    for (name, value) in headers.iter() {
        if name.as_str().to_lowercase() == "host" {
            continue;
        }
        reqwest_req = reqwest_req.header(name, value);
    }

    let res = reqwest_req
        .body(body_bytes)
        .send()
        .await
        .map_err(|_| StatusCode::BAD_GATEWAY)?;

    let mut axum_res = axum::http::Response::builder().status(res.status());
    
    for (name, value) in res.headers().iter() {
        axum_res = axum_res.header(name, value);
    }

    let stream = res.bytes_stream();
    let body = Body::from_stream(stream);

    let response = axum_res
        .body(body)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(response)
}
