//! Integration Test: Production Decoupling & Native Fallback Architecture
//! Verifies complete severance of the Python fallback reverse proxy, structured JSON 404 enforcement,
//! SPA static file resolution safeguards, and native Axum dual-mounted route verification.

use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use serde_json::Value;
use std::sync::{Arc, Mutex};
use tower::ServiceExt;

use rust_gateway_ffi::{
    routes::build_app_router,
    AppState,
};

async fn create_test_state() -> AppState {
    let pool = rust_gateway_ffi::db::DbPool::connect_lazy("sqlite::memory:").expect("lazy pool");
    let inference_manager = Arc::new(
        rust_gateway_ffi::ml::InferenceManager::new()
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("backend"))
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("../backend"))
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("."))
            .unwrap_or_else(|_| {
                rust_gateway_ffi::ml::InferenceManager::from_dir("backend")
                    .or_else(|_| rust_gateway_ffi::ml::InferenceManager::new())
                    .expect("fallback inference manager")
            }),
    );
    AppState {
        http_client: reqwest::Client::new(),
        db_pool: pool,
        secret_key: "test_secret_for_decoupling_tests".to_string(),
        sysinfo: Arc::new(Mutex::new(sysinfo::System::new())),
        vector_store: rust_gateway_ffi::vector_store::VectorStoreState::default(),
        inference_manager,
    }
}

#[tokio::test]
async fn test_unrecognized_api_route_returns_structured_json_404() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let response = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/nonexistent/lakehouse/endpoint")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    assert_eq!(
        response.headers().get("content-type").unwrap().to_str().unwrap(),
        "application/json"
    );

    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(json["error"], "Not Found");
    assert_eq!(json["message"], "Endpoint not recognized");
}

#[tokio::test]
async fn test_unrecognized_api_post_returns_structured_json_404() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/invalid/mutation")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"action":"unknown"}"#))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(json["error"], "Not Found");
    assert_eq!(json["message"], "Endpoint not recognized");
}

#[tokio::test]
async fn test_spa_navigation_serves_index_html_when_dist_present() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let response = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/appointments")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    // When frontend/dist is present in repo, browser SPA paths return index.html
    assert_eq!(response.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let html = String::from_utf8_lossy(&bytes);
    assert!(html.contains("<!doctype html>") || html.contains("<html") || html.contains("root"));
}

#[tokio::test]
async fn test_not_found_json_response_contract() {
    let response = rust_gateway_ffi::routes::not_found_json().await;
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(json["error"], "Not Found");
    assert_eq!(json["message"], "Endpoint not recognized");
}

#[tokio::test]
async fn test_root_endpoint_returns_json_metadata_for_api_clients() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let response = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/")
                .header("accept", "application/json")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(json["message"], "AI Healthcare API");
    assert_eq!(json["gateway"], "Rust Axum / Tokio PID 1 Native Engine");
    assert_eq!(json["version"], "3.0.0");
    assert!(json["timestamp"].is_string());
}

#[tokio::test]
async fn test_dual_mounted_lakehouse_router_resolves_natively() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // 1. Prefixed /v1/lakehouse/delta/history
    let res1 = app
        .clone()
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/history")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res1.status(), StatusCode::OK);

    // 2. Dual-mounted /lakehouse/delta/history
    let res2 = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/lakehouse/delta/history")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res2.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_mutating_verbs_on_unknown_routes_strictly_404() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    for method in &["PUT", "DELETE", "PATCH"] {
        let response = app
            .clone()
            .oneshot(
                Request::builder()
                    .method(*method)
                    .uri("/unknown-resource")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
        let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
        let json: Value = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(json["error"], "Not Found");
        assert_eq!(json["message"], "Endpoint not recognized");
    }
}
