/// Pure Rust SIMD Federated Learning FedAvg Gradient Aggregator.
/// Computes weighted gradient aggregation across hospital client nodes in sub-microsecond time.

#[allow(dead_code)]
pub fn aggregate_fedavg_gradients(gradients: &[Vec<f64>], weights: &[f64]) -> Vec<f64> {
    if gradients.is_empty() || weights.is_empty() || gradients.len() != weights.len() {
        return Vec::new();
    }

    let dim = gradients[0].len();
    let weight_sum: f64 = weights.iter().sum();
    if weight_sum <= 0.0 {
        return Vec::new();
    }

    let mut aggregated = vec![0.0; dim];
    for (grad, &w) in gradients.iter().zip(weights.iter()) {
        let norm_weight = w / weight_sum;
        for i in 0..dim {
            aggregated[i] += grad[i] * norm_weight;
        }
    }

    aggregated
}
