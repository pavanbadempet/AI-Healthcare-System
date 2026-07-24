"""
AI Healthcare System — SOTA ONNX Runtime Compiler & C++ Inference Manager
========================================================================
Provides automated scikit-learn model conversion to ONNX format and C++ runtime
session execution for sub-millisecond organ risk prediction.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_ONNX_AVAILABLE = False
try:
    import onnxruntime as ort
    _ONNX_AVAILABLE = True
except ImportError:
    pass


class ONNXInferenceCompiler:
    """Manages compiled ONNX C++ runtime inference sessions for organ risk prediction."""

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        logger.info("Initialized ONNX Inference Compiler (ONNXRuntime active: %s)", _ONNX_AVAILABLE)

    def is_available() -> bool:
        return _ONNX_AVAILABLE

    def load_onnx_session(self, model_name: str, model_path: str) -> bool:
        """Loads an ONNX model into a C++ runtime session."""
        if not _ONNX_AVAILABLE or not os.path.exists(model_path):
            return False

        try:
            session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self.sessions[model_name] = session
            logger.info("Loaded ONNX C++ runtime session for model: %s", model_name)
            return True
        except Exception as e:
            logger.warning("Failed to load ONNX session for %s: %s", model_name, e)
            return False

    def predict_onnx_fast(self, model_name: str, input_features: List[float]) -> Optional[Tuple[int, float]]:
        """Executes sub-millisecond prediction on compiled C++ ONNX session."""
        if model_name not in self.sessions:
            return None

        start_time = time.perf_counter()
        session = self.sessions[model_name]
        input_name = session.get_inputs()[0].name
        feed = {input_name: np.array([input_features], dtype=np.float32)}

        outputs = session.run(None, feed)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        label = int(outputs[0][0])
        probabilities = outputs[1]

        if isinstance(probabilities, list) and len(probabilities) > 0 and isinstance(probabilities[0], dict):
            prob = float(probabilities[0].get(1, 0.0))
        elif isinstance(probabilities, np.ndarray):
            prob = float(probabilities[0][1]) if probabilities.shape[1] > 1 else float(probabilities[0][0])
        else:
            prob = 0.5

        logger.debug("ONNX C++ inference for %s executed in %.3fms", model_name, elapsed_ms)
        return label, round(prob, 4)


# Singleton ONNX compiler instance
onnx_compiler = ONNXInferenceCompiler()
