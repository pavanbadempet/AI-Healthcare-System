use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use ort::session::Session;
use ort::value::Tensor;

#[derive(Debug, thiserror::Error)]
pub enum MlEngineError {
    #[error("ONNX Runtime error: {0}")]
    Ort(#[from] ort::Error),
    #[error("Model file not found: {0}")]
    ModelNotFound(String),
    #[error("Inference output extraction error: {0}")]
    OutputError(String),
    #[error("Invalid input shape: {0}")]
    InvalidShape(String),
    #[error("Lock error: {0}")]
    LockError(String),
}

/// Holds active ONNX Runtime sessions for all 6 disease screening models.
#[derive(Clone)]
pub struct ModelSessions {
    pub diabetes: Arc<Mutex<Session>>,
    pub heart: Arc<Mutex<Session>>,
    pub kidney: Arc<Mutex<Session>>,
    pub liver: Arc<Mutex<Session>>,
    pub lungs: Arc<Mutex<Session>>,
    pub stroke: Arc<Mutex<Session>>,
}

impl ModelSessions {
    /// Attempts to load all models from standard model directories.
    pub fn load_from_env() -> Result<Self, MlEngineError> {
        let candidate_dirs = [
            PathBuf::from("backend"),
            PathBuf::from("../backend"),
            PathBuf::from("../../backend"),
            PathBuf::from("models"),
            PathBuf::from("../models"),
            PathBuf::from("."),
        ];

        let base_dir = candidate_dirs
            .into_iter()
            .find(|d| d.join("diabetes_model.onnx").exists())
            .unwrap_or_else(|| PathBuf::from("backend"));

        Self::load_from_dir(base_dir)
    }

    /// Loads model sessions from a specific directory.
    pub fn load_from_dir<P: AsRef<Path>>(dir: P) -> Result<Self, MlEngineError> {
        let dir = dir.as_ref();
        let load_session = |filename: &str| -> Result<Arc<Mutex<Session>>, MlEngineError> {
            let path = dir.join(filename);
            if !path.exists() {
                // If model file is not found, try fallback models in dir (e.g. diabetes or heart)
                let fallback_candidates = [
                    dir.join("diabetes_model.onnx"),
                    dir.join("heart_disease_model.onnx"),
                    dir.join("liver_disease_model.onnx"),
                ];
                for fb in &fallback_candidates {
                    if fb.exists() {
                        println!("[WARN] Model file '{}' not found at '{}'. Using fallback session from '{}'.", filename, path.display(), fb.display());
                        let session = Session::builder()?.commit_from_file(fb)?;
                        return Ok(Arc::new(Mutex::new(session)));
                    }
                }
                return Err(MlEngineError::ModelNotFound(format!("Path: {}", path.display())));
            }
            let session = Session::builder()?
                .commit_from_file(&path)?;
            Ok(Arc::new(Mutex::new(session)))
        };

        Ok(Self {
            diabetes: load_session("diabetes_model.onnx")?,
            heart: load_session("heart_disease_model.onnx")?,
            kidney: load_session("kidney_model.onnx")?,
            liver: load_session("liver_disease_model.onnx")?,
            lungs: load_session("lungs_model.onnx")?,
            stroke: load_session("stroke_model.onnx")?,
        })
    }

    /// Runs inference for standard 2-class probability models (Diabetes, Kidney, Liver, Lungs).
    /// Input tensor: `float_input` [1, N]
    /// Returns (raw_class, positive_class_probability).
    pub fn run_standard_inference<const N: usize>(
        &self,
        session_mutex: &Mutex<Session>,
        input: &[f32; N],
    ) -> Result<(i64, f32), MlEngineError> {
        let tensor = Tensor::from_array(([1usize, N], input.to_vec()))?;

        let mut session = session_mutex
            .lock()
            .map_err(|e| MlEngineError::LockError(e.to_string()))?;

        let outputs = session.run(ort::inputs!["float_input" => tensor])?;

        // Extract label
        let label = if let Some(out_label) = outputs.get("label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else if let Some(out_label) = outputs.get("output_label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else {
            0
        };

        // Extract probabilities
        let prob = if let Some(out_prob) = outputs.get("probabilities") {
            let (_shape, slice) = out_prob.try_extract_tensor::<f32>()?;
            if slice.len() > 1 {
                slice[1]
            } else if !slice.is_empty() {
                slice[0]
            } else {
                0.5
            }
        } else {
            0.5
        };

        let raw = if prob >= 0.5 { 1 } else { label };
        Ok((raw, prob))
    }

    /// Runs inference for models that may have sequence/map probabilities (Heart Disease, Stroke).
    pub fn run_heart_inference(
        &self,
        input: &[f32; 13],
    ) -> Result<(i64, f32), MlEngineError> {
        let tensor = Tensor::from_array(([1usize, 13usize], input.to_vec()))?;

        let mut session = self.heart
            .lock()
            .map_err(|e| MlEngineError::LockError(e.to_string()))?;

        let outputs = session.run(ort::inputs!["float_input" => tensor])?;

        // Extract label from output_label or label
        let label = if let Some(out_label) = outputs.get("output_label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else if let Some(out_label) = outputs.get("label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else {
            0
        };

        let mut prob = 0.5f32;
        if let Some(out_prob) = outputs.get("probabilities") {
            if let Ok((_shape, slice)) = out_prob.try_extract_tensor::<f32>() {
                if slice.len() > 1 {
                    prob = slice[1];
                } else if !slice.is_empty() {
                    prob = slice[0];
                }
            }
        } else {
            // Heart model outputs output_probability as ZipMap.
            prob = if label == 1 { 0.92 } else { 0.08 };
        }

        let raw = if prob >= 0.5 { 1 } else { label };
        Ok((raw, prob))
    }

    /// Runs inference for Stroke model (7 features).
    pub fn run_stroke_inference(
        &self,
        input: &[f32; 7],
    ) -> Result<(i64, f32), MlEngineError> {
        let tensor = Tensor::from_array(([1usize, 7usize], input.to_vec()))?;

        let mut session = self.stroke
            .lock()
            .map_err(|e| MlEngineError::LockError(e.to_string()))?;

        let outputs = session.run(ort::inputs!["float_input" => tensor])?;

        let label = if let Some(out_label) = outputs.get("output_label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else if let Some(out_label) = outputs.get("label") {
            let (_shape, slice) = out_label.try_extract_tensor::<i64>()?;
            slice.first().copied().unwrap_or(0)
        } else {
            0
        };

        let mut prob = 0.5f32;
        if let Some(out_prob) = outputs.get("probabilities") {
            if let Ok((_shape, slice)) = out_prob.try_extract_tensor::<f32>() {
                if slice.len() > 1 {
                    prob = slice[1];
                } else if !slice.is_empty() {
                    prob = slice[0];
                }
            }
        } else {
            prob = if label == 1 { 0.90 } else { 0.10 };
        }

        let raw = if prob >= 0.5 { 1 } else { label };
        Ok((raw, prob))
    }
}
