use axum::{
    extract::State,
    response::IntoResponse,
    Router,
    routing::get,
};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct SystemMetrics {
    pub timestamp: String,
    pub cpu_usage_percent: f32,
    pub ram_usage_percent: f64,
    pub total_memory_mb: u64,
    pub used_memory_mb: u64,
    pub active_db_connections: u32,
    pub ipc_mode: String,
}

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/health", get(get_system_health))
}

async fn get_system_health(
    State(state): State<crate::AppState>,
    headers: axum::http::HeaderMap,
) -> impl IntoResponse {
    let mut sys = state.sysinfo.lock().unwrap();
    sys.refresh_all();

    // Get CPU usage across all cores
    let cpu_usage = sys.global_cpu_usage();

    // Get Memory stats
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let ram_percent = if total_mem > 0 {
        (used_mem as f64 / total_mem as f64) * 100.0
    } else {
        0.0
    };

    let total_mb = total_mem / 1024 / 1024;
    let used_mb = used_mem / 1024 / 1024;

    // Get database pool stats (SQLx pool size)
    let active_conns = state.db_pool.size();

    let timestamp = chrono::Utc::now().to_rfc3339();

    #[cfg(unix)]
    let ipc_mode = "Unix Socket (UDS)".to_string();
    #[cfg(not(unix))]
    let ipc_mode = "TCP Loopback (Tuned)".to_string();

    let metrics = SystemMetrics {
        timestamp,
        cpu_usage_percent: cpu_usage,
        ram_usage_percent: ram_percent,
        total_memory_mb: total_mb,
        used_memory_mb: used_mb,
        active_db_connections: active_conns,
        ipc_mode,
    };

    crate::codec::serialize_adaptive(metrics, &headers)
}

#[cfg(test)]
mod tests {
    use sysinfo::System;
    use super::*;

    #[tokio::test]
    async fn test_system_collection() {
        let mut sys = System::new_all();
        sys.refresh_all();
        assert!(sys.total_memory() > 0);
    }

    #[test]
    fn test_adaptive_msgpack_serialization() {
        use axum::http::HeaderMap;
        let mut headers = HeaderMap::new();
        headers.insert("accept", "application/x-msgpack".parse().unwrap());
        
        let metrics = SystemMetrics {
            timestamp: "2026-07-16T00:00:00Z".to_string(),
            cpu_usage_percent: 1.5,
            ram_usage_percent: 45.2,
            total_memory_mb: 16000,
            used_memory_mb: 8000,
            active_db_connections: 3,
            ipc_mode: "Test Mode".to_string(),
        };

        let response = crate::codec::serialize_adaptive(metrics, &headers);
        assert_eq!(response.headers().get("content-type").unwrap().to_str().unwrap(), "application/x-msgpack");
    }
}
