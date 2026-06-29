import * as ort from 'onnxruntime-web';

// Set up CDN path for WebAssembly files if not found locally
ort.env.wasm.numThreads = 1;

interface ModelSessionCache {
  model: ort.InferenceSession | null;
  scaler: ort.InferenceSession | null;
}

const sessions: Record<string, ModelSessionCache> = {
  diabetes: { model: null, scaler: null },
  heart: { model: null, scaler: null },
  liver: { model: null, scaler: null },
  kidney: { model: null, scaler: null },
  lungs: { model: null, scaler: null },
};

async function getOrInitSession(modelName: string): Promise<ModelSessionCache> {
  const cache = sessions[modelName];
  if (cache.model) return cache;

  const isWebGPUAvailable = typeof navigator !== 'undefined' && 'gpu' in navigator;
  const options: ort.InferenceSession.SessionOptions = {
    executionProviders: isWebGPUAvailable ? ['webgpu', 'wasm'] : ['wasm'],
    graphOptimizationLevel: 'all' // Enable graph optimizations (operator fusion, constant folding)
  };

  try {
    console.log(`[ONNX] Loading sessions for ${modelName} (WebGPU supported: ${isWebGPUAvailable})...`);
    if (modelName === 'diabetes') {
      cache.model = await ort.InferenceSession.create('/models/diabetes.onnx', options);
    } else if (modelName === 'heart') {
      cache.model = await ort.InferenceSession.create('/models/heart.onnx', options);
    } else if (modelName === 'liver') {
      cache.scaler = await ort.InferenceSession.create('/models/liver_scaler.onnx', options);
      cache.model = await ort.InferenceSession.create('/models/liver_disease_model.onnx', options);
    } else if (modelName === 'kidney') {
      cache.scaler = await ort.InferenceSession.create('/models/kidney_scaler.onnx', options);
      cache.model = await ort.InferenceSession.create('/models/kidney_model.onnx', options);
    } else if (modelName === 'lungs') {
      cache.scaler = await ort.InferenceSession.create('/models/lungs_scaler.onnx', options);
      cache.model = await ort.InferenceSession.create('/models/lungs_model.onnx', options);
    }
    console.log(`[ONNX] Successfully loaded sessions for ${modelName}`);

    // JIT Warmup run to compile WebGPU shading pipelines and prevent runtime cold start delays
    try {
      const numFeatures = modelName === 'diabetes' || modelName === 'heart' ? 9
                        : modelName === 'liver' ? 10
                        : modelName === 'kidney' ? 24
                        : 22; // lungs has 22 features
      const dummyInput = new Float32Array(numFeatures).fill(0.0);
      let runInput: any = dummyInput;

      // If a scaler is present, warm it up first
      if (cache.scaler) {
        const dummyTensor = new ort.Tensor('float32', dummyInput, [1, numFeatures]);
        const scalerOutputs = await cache.scaler.run({ [cache.scaler.inputNames[0]]: dummyTensor });
        runInput = scalerOutputs[cache.scaler.outputNames[0]].data;
      }

      if (cache.model) {
        const dummyTensor = new ort.Tensor('float32', runInput, [1, runInput.length]);
        await cache.model.run({ [cache.model.inputNames[0]]: dummyTensor });
        console.log(`[ONNX] WebGPU JIT warmup run completed for ${modelName}`);
      }
    } catch (warmupErr) {
      console.warn(`[ONNX] Warmup run bypassed or failed for ${modelName}:`, warmupErr);
    }
  } catch (err) {
    console.error(`[ONNX] Failed to load sessions for ${modelName}:`, err);
    throw err;
  }

  return cache;
}

/**
 * Perform client-side WASM inference for a given model.
 */
export async function runClientInference(
  modelName: string,
  rawFeatures: number[]
): Promise<{ prediction: string; probability: number; confidence: number; risk_level: string; raw: number }> {
  const cache = await getOrInitSession(modelName);
  if (!cache.model) {
    throw new Error(`ONNX model session for ${modelName} is not initialized.`);
  }

  let finalFeatures = Float32Array.from(rawFeatures);

  // Apply model-specific scaling and pre-processing
  if (modelName === 'liver') {
    // Apply log1p to skewed features: total_bilirubin (2), alkaline_phosphotase (4), alamine_aminotransferase (5), albumin_and_globulin_ratio (9)
    // Indices: total_bilirubin is index 2, alkphos is index 4, alamine is index 5, ratio is index 9
    const skewedIndices = [2, 4, 5, 9];
    for (const idx of skewedIndices) {
      if (rawFeatures[idx] !== undefined) {
        rawFeatures[idx] = Math.log1p(rawFeatures[idx]);
      }
    }
    finalFeatures = Float32Array.from(rawFeatures);
  }

  // Run Scaler if present
  if (cache.scaler) {
    const scalerTensor = new ort.Tensor('float32', finalFeatures, [1, rawFeatures.length]);
    const scalerOutputs = await cache.scaler.run({ [cache.scaler.inputNames[0]]: scalerTensor });
    const scaledOutputName = cache.scaler.outputNames[0];
    const scaledData = scalerOutputs[scaledOutputName].data as Float32Array;
    finalFeatures = Float32Array.from(scaledData);
  }

  // Run Model
  const modelTensor = new ort.Tensor('float32', finalFeatures, [1, finalFeatures.length]);
  const modelOutputs = await cache.model.run({ [cache.model.inputNames[0]]: modelTensor });
  
  // Parse outputs
  const outputNames = cache.model.outputNames;
  
  // Standard scikit-learn ONNX models return:
  // - output_label (classification label)
  // - output_probability (sequence of maps containing class probabilities)
  let probability = 0.5;
  let predictionLabel = 0;

  try {
    if (outputNames.length >= 2) {
      // Typically outputNames[0] is label, outputNames[1] is probability map/tensor
      const probabilities = modelOutputs[outputNames[1]];
      if (probabilities && probabilities.data) {
        if (probabilities.type === 'float32') {
          // Output probabilities is a 2D float array [1, 2]
          const probData = probabilities.data as Float32Array;
          probability = probData[1] !== undefined ? probData[1] : probData[0];
        } else if (Array.isArray((probabilities as any).value)) {
          // Model outputs dictionary sequence
          const val = (probabilities as any).value[0];
          if (val instanceof Map) {
            probability = val.get(1) || val.get('1') || 0.5;
          } else if (typeof val === 'object' && val !== null) {
            probability = (val as any)['1'] !== undefined ? (val as any)['1'] : 0.5;
          }
        }
      }
      
      const labelOutput = modelOutputs[outputNames[0]];
      if (labelOutput && labelOutput.data) {
        predictionLabel = Number(labelOutput.data[0]);
      }
    } else {
      // Fallback for single output regression/classification
      const singleOutput = modelOutputs[outputNames[0]];
      if (singleOutput && singleOutput.data) {
        const outVal = Number(singleOutput.data[0]);
        if (outVal <= 1) {
          probability = outVal;
          predictionLabel = probability >= 0.5 ? 1 : 0;
        } else {
          predictionLabel = outVal;
        }
      }
    }
  } catch (err) {
    console.warn('[ONNX WASM] Error parsing probabilities, falling back to thresholding:', err);
    predictionLabel = probability >= 0.5 ? 1 : 0;
  }

  // Classify risk level and compute confidence
  const confidence = Math.round(probability * 100 * 10) / 10;
  let risk_level = 'Low';
  if (confidence >= 75) {
    risk_level = 'High';
  } else if (confidence >= 40) {
    risk_level = 'Moderate';
  }

  let predictionText = 'Healthy';
  if (predictionLabel === 1) {
    if (modelName === 'diabetes') predictionText = 'High Risk';
    else if (modelName === 'heart') predictionText = 'Heart Disease Detected';
    else if (modelName === 'liver') predictionText = 'Liver Disease Detected';
    else if (modelName === 'kidney') predictionText = 'Chronic Kidney Disease Detected';
    else if (modelName === 'lungs') predictionText = 'Respiratory Issue Detected';
  } else {
    if (modelName === 'diabetes') predictionText = 'Low Risk';
    else if (modelName === 'heart') predictionText = 'Healthy Heart';
    else if (modelName === 'liver') predictionText = 'Healthy Liver';
    else if (modelName === 'kidney') predictionText = 'Healthy Kidney';
    else if (modelName === 'lungs') predictionText = 'Healthy Lungs';
  }

  return {
    prediction: predictionText,
    probability,
    confidence,
    risk_level,
    raw: predictionLabel,
  };
}
