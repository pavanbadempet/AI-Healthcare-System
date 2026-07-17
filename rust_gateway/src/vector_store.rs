use axum::{routing::post, Json, Router};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;
use rayon::prelude::*;
use arc_swap::ArcSwap;

#[derive(Serialize, Deserialize, Clone, Debug, rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)]
#[archive(compare(PartialEq))]
#[archive_attr(derive(Debug))]
pub struct VectorRecord {
    pub id: String,
    pub vector: Vec<f32>,
    pub text: String,
    pub metadata_json: String,
}

#[derive(Clone)]
pub struct VectorStoreState {
    pub records: Arc<ArcSwap<Vec<VectorRecord>>>,
}

impl Default for VectorStoreState {
    fn default() -> Self {
        Self {
            records: Arc::new(ArcSwap::new(Arc::new(Vec::new()))),
        }
    }
}

#[derive(Deserialize, Debug)]
pub struct AddPayload {
    pub id: String,
    pub vector: Vec<f32>,
    pub text: String,
    pub metadata: Value,
}

#[derive(Deserialize, Debug)]
pub struct SearchPayload {
    pub query_vector: Vec<f32>,
    pub n_results: usize,
    pub user_id: Option<String>,
    pub facility_id: Option<String>,
}

#[derive(Serialize, Debug)]
pub struct SearchResult {
    pub id: String,
    pub text: String,
    pub metadata: Value,
    pub score: f32,
}

pub fn router(state: VectorStoreState) -> Router<crate::AppState> {
    Router::new()
        .route("/add", post(add_handler))
        .route("/search", post(search_handler))
        .with_state(state)
}

async fn add_handler(
    axum::extract::State(state): axum::extract::State<VectorStoreState>,
    Json(payload): Json<AddPayload>,
) -> axum::http::StatusCode {
    let metadata_str = payload.metadata.to_string();
    
    // Lock-free write: clone current vec, modify it, and swap pointer atomically
    let current = state.records.load();
    let mut new_records = (**current).clone();
    
    new_records.retain(|r| r.id != payload.id);
    new_records.push(VectorRecord {
        id: payload.id,
        vector: payload.vector,
        text: payload.text,
        metadata_json: metadata_str,
    });
    
    state.records.store(Arc::new(new_records));
    
    axum::http::StatusCode::OK
}

async fn search_handler(
    axum::extract::State(state): axum::extract::State<VectorStoreState>,
    Json(payload): Json<SearchPayload>,
) -> Json<Vec<SearchResult>> {
    // Lock-free read: load the atomically tracked vector pointer instantly
    let records = state.records.load();
    
    let mut matches: Vec<SearchResult> = records
        .par_iter()
        .filter_map(|r| {
            // Parse metadata back on demand
            let meta_val: Value = serde_json::from_str(&r.metadata_json).unwrap_or(Value::Null);
            
            // Filter by user_id and facility_id in metadata if provided
            if let Some(ref uid) = payload.user_id {
                if let Some(record_uid) = meta_val.get("user_id").and_then(|v| v.as_str()) {
                    if record_uid != uid {
                        return None;
                    }
                }
            }
            if let Some(ref fid) = payload.facility_id {
                if let Some(record_fid) = meta_val.get("facility_id").and_then(|v| v.as_str()) {
                    if record_fid != fid {
                        return None;
                    }
                }
            }
            
            let score = cosine_similarity(&payload.query_vector, &r.vector);
            Some(SearchResult {
                id: r.id.clone(),
                text: r.text.clone(),
                metadata: meta_val,
                score,
            })
        })
        .collect();
    
    // Sort descending by score
    matches.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    matches.truncate(payload.n_results);
    
    Json(matches)
}

// Runtime feature detection for AVX2 explicit SIMD calculation
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
    {
        if is_x86_feature_detected!("avx2") {
            return unsafe { cosine_similarity_avx2(a, b) };
        }
    }
    cosine_similarity_fallback(a, b)
}

#[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
#[target_feature(enable = "avx2")]
unsafe fn cosine_similarity_avx2(a: &[f32], b: &[f32]) -> f32 {
    use std::arch::x86_64::*;
    
    let len = a.len();
    if len != b.len() || len == 0 {
        return 0.0;
    }
    
    let mut i = 0;
    let mut dot_sum = _mm256_setzero_ps();
    let mut norm_a_sum = _mm256_setzero_ps();
    let mut norm_b_sum = _mm256_setzero_ps();
    
    while i + 8 <= len {
        unsafe {
            let va = _mm256_loadu_ps(a.as_ptr().add(i));
            let vb = _mm256_loadu_ps(b.as_ptr().add(i));
            
            dot_sum = _mm256_add_ps(dot_sum, _mm256_mul_ps(va, vb));
            norm_a_sum = _mm256_add_ps(norm_a_sum, _mm256_mul_ps(va, va));
            norm_b_sum = _mm256_add_ps(norm_b_sum, _mm256_mul_ps(vb, vb));
        }
        i += 8;
    }
    
    let mut temp_dot = [0.0f32; 8];
    let mut temp_na = [0.0f32; 8];
    let mut temp_nb = [0.0f32; 8];
    
    unsafe {
        _mm256_storeu_ps(temp_dot.as_mut_ptr(), dot_sum);
        _mm256_storeu_ps(temp_na.as_mut_ptr(), norm_a_sum);
        _mm256_storeu_ps(temp_nb.as_mut_ptr(), norm_b_sum);
    }
    
    let mut dot = temp_dot.iter().sum::<f32>();
    let mut norm_a = temp_na.iter().sum::<f32>();
    let mut norm_b = temp_nb.iter().sum::<f32>();
    
    while i < len {
        let val_a = a[i];
        let val_b = b[i];
        dot += val_a * val_b;
        norm_a += val_a * val_a;
        norm_b += val_b * val_b;
        i += 1;
    }
    
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        let denom = norm_a.sqrt() * norm_b.sqrt();
        if denom <= 1e-10 {
            0.0
        } else {
            dot / denom
        }
    }
}

fn cosine_similarity_fallback(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    let len = a.len();
    let mut dot = 0.0;
    let mut norm_a = 0.0;
    let mut norm_b = 0.0;
    for i in 0..len {
        let val_a = a[i];
        let val_b = b[i];
        dot += val_a * val_b;
        norm_a += val_a * val_a;
        norm_b += val_b * val_b;
    }
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        let denom = norm_a.sqrt() * norm_b.sqrt();
        if denom <= 1e-10 {
            0.0
        } else {
            dot / denom
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity() {
        let a = vec![1.0, 0.0, 0.0];
        let b = vec![1.0, 0.0, 0.0];
        assert!((cosine_similarity(&a, &b) - 1.0).abs() < 1e-5);

        let c = vec![0.0, 1.0, 0.0];
        assert!(cosine_similarity(&a, &c).abs() < 1e-5);
    }
}
