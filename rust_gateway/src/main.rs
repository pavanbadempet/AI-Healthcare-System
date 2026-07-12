use axum::{
    body::Body,
    extract::{Request, State},
    http::{uri::Uri, StatusCode},
    response::{IntoResponse, Response},
    routing::{any, get, post},
    Json, Router,
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;

#[derive(Clone)]
struct AppState {
    http_client: Client,
    python_backend_url: String,
}

#[tokio::main]
async fn main() {
    println!("Starting Rust API Gateway...");

    let state = AppState {
        http_client: Client::new(),
        python_backend_url: "http://127.0.0.1:8001".to_string(), // Python server port
    };

    let app = Router::new()
        // Rust native routes will go here
        .route("/healthz_rust", get(health_check))
        .route("/v1/auth/login_stub", post(login_stub))
        // Fallback proxy to Python backend
        .fallback(any(proxy_handler))
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

#[derive(Serialize)]
struct LoginResponse {
    message: String,
}

// Temporary stub for auth before we implement the SQLite database connection
async fn login_stub() -> Json<LoginResponse> {
    Json(LoginResponse {
        message: "Rust login stub active. DB integration pending.".to_string(),
    })
}

use axum::body::Bytes;
use http_body_util::BodyExt; // For `into_data_stream()` if needed, but simpler is just to collect bytes

// The core reverse proxy function
async fn proxy_handler(
    State(state): State<AppState>,
    mut req: Request,
) -> Result<Response, StatusCode> {
    let path = req.uri().path();
    let path_query = req
        .uri()
        .path_and_query()
        .map(|v| v.as_str())
        .unwrap_or(path);

    let uri = format!("{}{}", state.python_backend_url, path_query);

    let method = req.method().clone();
    let headers = req.headers().clone();
    
    // For simplicity in this PoC, we collect the entire body into memory before forwarding.
    // In production, you would stream this via reqwest::Body::wrap_stream
    let body_bytes = req.into_body().collect().await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.to_bytes();

    println!("Proxying request to: {}", uri);

    let mut reqwest_req = state.http_client.request(method, uri);
    
    for (name, value) in headers.iter() {
        // Skip host header so reqwest sets it properly
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

    // Convert reqwest stream to axum body
    let stream = res.bytes_stream();
    let body = Body::from_stream(stream);

    let response = axum_res
        .body(body)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(response)
}
