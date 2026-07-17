use axum::{
    http::{header, HeaderMap, StatusCode},
    response::{IntoResponse, Response},
};
use serde::{Deserialize, Serialize};

pub fn serialize_adaptive<T>(data: T, headers: &HeaderMap) -> Response
where
    T: Serialize,
{
    let accept_msgpack = headers
        .get(header::ACCEPT)
        .and_then(|h| h.to_str().ok())
        .map(|s| s.contains("application/x-msgpack"))
        .unwrap_or(false);

    if accept_msgpack {
        match rmp_serde::to_vec(&data) {
            Ok(bytes) => (
                [
                    (header::CONTENT_TYPE, "application/x-msgpack"),
                ],
                bytes,
            ).into_response(),
            Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
        }
    } else {
        match serde_json::to_vec(&data) {
            Ok(bytes) => (
                [
                    (header::CONTENT_TYPE, "application/json"),
                ],
                bytes,
            ).into_response(),
            Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
        }
    }
}

#[allow(dead_code)]
pub fn deserialize_adaptive<'a, T>(bytes: &'a [u8], headers: &HeaderMap) -> Result<T, StatusCode>
where
    T: Deserialize<'a>,
{
    let is_msgpack = headers
        .get(header::CONTENT_TYPE)
        .and_then(|h| h.to_str().ok())
        .map(|s| s.contains("application/x-msgpack"))
        .unwrap_or(false);

    if is_msgpack {
        rmp_serde::from_slice(bytes).map_err(|_| StatusCode::BAD_REQUEST)
    } else {
        serde_json::from_slice(bytes).map_err(|_| StatusCode::BAD_REQUEST)
    }
}
