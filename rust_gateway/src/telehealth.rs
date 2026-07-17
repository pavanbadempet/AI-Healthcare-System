use axum::{
    http::StatusCode,
    response::IntoResponse,
    Json, Router,
    routing::post,
};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TelehealthSession {
    pub session_id: String,
    pub patient_id: String,
    pub provider_id: String,
    pub room_name: String,
    pub status: String,
    pub started_at: Option<f64>,
    pub ended_at: Option<f64>,
    pub duration_minutes: f64,
    pub quality_log: QualityLog,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct QualityLog {
    pub packet_loss_percentage: f64,
    pub average_latency_ms: f64,
    pub quality_rating: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateSessionPayload {
    pub session_id: String,
    pub patient_id: String,
    pub provider_id: String,
    pub room_name: String,
}

#[derive(Debug, Deserialize)]
pub struct TokenRequestPayload {
    pub room_name: String,
    pub user_id: String,
    pub role: String,
}

#[derive(Debug, Serialize)]
pub struct TokenResponse {
    pub room_name: String,
    pub user_id: String,
    pub role: String,
    pub token_type: String,
    pub access_token: String,
    pub expires_in_seconds: u32,
}

#[derive(Debug, Deserialize)]
pub struct QualityRequestPayload {
    pub packet_loss: f64,
    pub latency_ms: f64,
}

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/session", post(create_session))
        .route("/session/token", post(generate_token))
        .route("/session/quality", post(audit_quality))
}

async fn create_session(
    Json(payload): Json<CreateSessionPayload>,
) -> impl IntoResponse {
    let session = TelehealthSession {
        session_id: payload.session_id,
        patient_id: payload.patient_id,
        provider_id: payload.provider_id,
        room_name: payload.room_name,
        status: "scheduled".to_string(),
        started_at: None,
        ended_at: None,
        duration_minutes: 0.0,
        quality_log: QualityLog {
            packet_loss_percentage: 0.0,
            average_latency_ms: 0.0,
            quality_rating: "EXCELLENT".to_string(),
        },
    };
    (StatusCode::CREATED, Json(session))
}

async fn generate_token(
    Json(payload): Json<TokenRequestPayload>,
) -> impl IntoResponse {
    // raw_signature = f"{self.room_name}:{user_id}:{role}:secure-salt-key-12345"
    let raw_signature = format!("{}:{}:{}:secure-salt-key-12345", payload.room_name, payload.user_id, payload.role);
    let mut hasher = Sha256::new();
    hasher.update(raw_signature.as_bytes());
    let token = format!("{:x}", hasher.finalize());

    let response = TokenResponse {
        room_name: payload.room_name,
        user_id: payload.user_id,
        role: payload.role,
        token_type: "Bearer WebRTC-Signaling".to_string(),
        access_token: format!("jwt-webrtc-{}", &token[..32]),
        expires_in_seconds: 3600,
    };
    (StatusCode::OK, Json(response))
}

async fn audit_quality(
    Json(payload): Json<QualityRequestPayload>,
) -> impl IntoResponse {
    let rating = if payload.packet_loss > 5.0 || payload.latency_ms > 250.0 {
        "POOR".to_string()
    } else if payload.packet_loss > 1.0 || payload.latency_ms > 100.0 {
        "FAIR".to_string()
    } else {
        "EXCELLENT".to_string()
    };

    let log = QualityLog {
        packet_loss_percentage: payload.packet_loss,
        average_latency_ms: payload.latency_ms,
        quality_rating: rating,
    };
    (StatusCode::OK, Json(log))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_session() {
        let payload = CreateSessionPayload {
            session_id: "sess-1".to_string(),
            patient_id: "pat-1".to_string(),
            provider_id: "prov-1".to_string(),
            room_name: "room-1".to_string(),
        };
        let response = create_session(Json(payload)).await.into_response();
        assert_eq!(response.status(), StatusCode::CREATED);
    }

    #[tokio::test]
    async fn test_generate_token() {
        let payload = TokenRequestPayload {
            room_name: "Consult-Room-99".to_string(),
            user_id: "patient-44".to_string(),
            role: "patient".to_string(),
        };
        let response = generate_token(Json(payload)).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn test_audit_quality() {
        let payload = QualityRequestPayload {
            packet_loss: 0.2,
            latency_ms: 45.0,
        };
        let response = audit_quality(Json(payload)).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);

        let payload_poor = QualityRequestPayload {
            packet_loss: 6.5,
            latency_ms: 300.0,
        };
        let response_poor = audit_quality(Json(payload_poor)).await.into_response();
        assert_eq!(response_poor.status(), StatusCode::OK);
    }
}
