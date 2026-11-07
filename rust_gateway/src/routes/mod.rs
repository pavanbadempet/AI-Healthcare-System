use axum::{
    extract::Request,
    http::{Method, StatusCode, Uri},
    response::{IntoResponse, Response},
    routing::get,
    Json, Router,
};
use serde_json::json;
use std::path::PathBuf;

// Platform & Admin Route Modules
pub mod admin;
pub mod data_platform;
pub mod fhir;
pub mod lakehouse;
pub mod licensing;
pub mod smart;
pub mod top_level;

// Clinical & Hospital Route Modules
pub mod appointments;
pub mod billing;
pub mod care_events;
pub mod diagnostics;
pub mod discharge;
pub mod hospital;
pub mod monitoring;
pub mod nursing;
pub mod pharmacy;

// AI, ML, Auth & Real-Time Intelligence Route Modules
pub mod auth;
pub mod chat;
pub mod federated;
pub mod governance;
pub mod intelligence;
pub mod prediction;
pub mod telemetry;

use crate::AppState;

/// Resolves the production frontend/dist directory across development, container, and CI layouts.
pub fn find_frontend_dist() -> Option<PathBuf> {
    if let Ok(env_path) = std::env::var("FRONTEND_DIST") {
        let p = PathBuf::from(env_path);
        if p.is_dir() {
            return Some(p);
        }
    }
    for candidate in &["frontend/dist", "../frontend/dist", "dist"] {
        let p = PathBuf::from(candidate);
        if p.is_dir() {
            return Some(p);
        }
    }
    None
}

/// Standardized structured JSON 404 response required by the Universe Dex API contract.
pub async fn not_found_json() -> Response {
    (
        StatusCode::NOT_FOUND,
        Json(json!({
            "error": "Not Found",
            "message": "Endpoint not recognized"
        })),
    )
        .into_response()
}

/// Native Axum fallback handler:
/// 1. Unrecognized API endpoints (/v1/*, /api/*, /healthz/*) and non-GET requests strictly return JSON 404.
/// 2. In headless environments (no frontend/dist), returns JSON 404.
/// 3. When frontend/dist is present:
///    - Serves static asset files directly.
///    - Falls back to index.html for React SPA client-side routing.
pub async fn gateway_fallback_handler(
    uri: Uri,
    method: Method,
    req: Request,
) -> Response {
    let path = uri.path();

    // 1. Any unrecognized API endpoint or mutating HTTP verb strictly returns JSON 404
    if path.starts_with("/v1")
        || path.starts_with("/api")
        || path.starts_with("/healthz")
        || path.starts_with("/.well-known")
        || (method != Method::GET && method != Method::HEAD)
    {
        return not_found_json().await;
    }

    // 2. Static SPA resolution when frontend/dist is present
    if let Some(dist_dir) = find_frontend_dist() {
        let index_file = dist_dir.join("index.html");

        if index_file.is_file() {
            use tower::Service;

            let mut serve_service = tower_http::services::ServeDir::new(&dist_dir)
                .fallback(tower_http::services::ServeFile::new(&index_file));

            match serve_service.call(req).await {
                Ok(response) => return response.into_response(),
                Err(_) => return not_found_json().await,
            }
        }
    }

    // 3. Graceful headless test mode fallback
    not_found_json().await
}

/// Master router builder that combines all domain sub-routers into a unified Axum router.
pub fn build_app_router(state: AppState) -> Router {
    let mut router = Router::new()
        // Top-level & System routes: /, /healthz, /healthz/*, /metrics, /generate_report, /v1/demo-readiness
        .merge(top_level::router())
        
        // SMART on FHIR standard discovery configuration endpoint
        .route(
            "/.well-known/smart-configuration",
            get(smart::well_known_smart_configuration),
        )
        
        // Platform domain sub-routers
        .nest("/v1/fhir", fhir::router())
        .nest("/v1/smart", smart::router())
        .nest("/api/v1/data-platform", data_platform::router())
        .nest("/v1/lakehouse", lakehouse::router())
        .nest("/lakehouse", lakehouse::router())
        .nest("/v1/licensing", licensing::router())
        .nest("/v1/admin", admin::router())
        
        // Clinical & Operational domain sub-routers
        .nest("/v1/appointments", appointments::router())
        .nest("/v1/hospital", hospital::router())
        .nest("/v1/billing", billing::router())
        .nest("/v1/pharmacy", pharmacy::router())
        .nest("/v1/diagnostics", diagnostics::router())
        .nest("/v1/nursing", nursing::router())
        .nest("/v1/monitoring", monitoring::router())
        .nest("/v1/discharge", discharge::router())
        .nest("/v1/events", care_events::router())
        
        // AI, ML, Auth & Real-Time Intelligence Route Modules
        .nest("/v1/auth", auth::router())
        .nest("/v1", auth::router())
        .merge(auth::router())
        .nest("/v1/predict", prediction::router())
        .nest("/v1/chat", chat::router())
        .nest("/v1", chat::router())
        .nest("/v1/intelligence", intelligence::router())
        .nest("/v1/governance", governance::router())
        .nest("/v1/federated", federated::router())
        .nest("/v1/telemetry", telemetry::router())
        
        // Legacy & complementary native sub-routers
        .nest("/v1/telehealth", crate::telehealth::router())
        .nest("/v1/claims", crate::claims::router())
        .nest("/v1/interop/fhir", crate::fhir::router())
        .nest("/v1/interop/vector-store", crate::vector_store::router(state.vector_store.clone()));

    // Mount high-performance static asset directory if built
    if let Some(dist_dir) = find_frontend_dist() {
        let assets_dir = dist_dir.join("assets");
        if assets_dir.is_dir() {
            router = router.nest_service(
                "/assets",
                tower_http::services::ServeDir::new(assets_dir),
            );
        }
    }

    // Attach native 404 fallback & static SPA routing (zero Python proxying)
    router
        .fallback(gateway_fallback_handler)
        .layer(tower_http::compression::CompressionLayer::new())
        .layer(tower_http::cors::CorsLayer::permissive())
        .with_state(state)
}
