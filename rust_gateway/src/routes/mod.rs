use axum::{
    routing::get,
    Router,
};

// Platform & Admin Route Modules
pub mod admin;
pub mod data_platform;
pub mod fhir;
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

/// Master router builder that combines all domain sub-routers into a unified Axum router.
pub fn build_app_router(state: AppState) -> Router {
    let router = Router::new()
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
        .nest("/v1/interop/vector-store", crate::vector_store::router(state.vector_store.clone()))
        
        // Fallback proxy to Python backend for any unhandled routes
        .fallback(crate::proxy_handler_fallback)
        .layer(tower_http::compression::CompressionLayer::new())
        .layer(tower_http::cors::CorsLayer::permissive())
        .with_state(state);

    router
}
