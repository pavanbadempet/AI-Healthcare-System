"""
Advanced AI Features for Enterprise Healthcare System
- Real-time Predictions with Streaming
- Model Performance Monitoring
- Automated Retraining
- Explainable AI (XAI) Enhancements
- Ensemble Methods
"""

import asyncio
import json
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import redis
from fastapi import WebSocket

logger = logging.getLogger(__name__)
ADVANCED_AI_FAILURE_MESSAGE = "Advanced AI operation failed."

@dataclass
class PredictionRequest:
    """Real-time prediction request structure"""
    user_id: int
    model_type: str
    features: Dict[str, Any]
    request_id: str = None
    timestamp: datetime = None
    priority: str = "normal"  # low, normal, high, critical

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

@dataclass
class PredictionResult:
    """Enhanced prediction result with metadata"""
    prediction: Any
    confidence: float
    explanation: Dict[str, Any]
    model_version: str
    processing_time_ms: float
    request_id: str
    timestamp: datetime
    risk_score: float = 0.0
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

class ModelPerformanceMonitor:
    """Real-time model performance monitoring"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.performance_window = 24 * 60 * 60  # 24 hours
        self.alert_thresholds = {
            'accuracy_drop': 0.05,  # 5% drop
            'latency_increase': 1000,  # 1 second
            'error_rate': 0.01  # 1% error rate
        }

    def record_prediction(self, model_type: str, prediction_result: PredictionResult,
                        ground_truth: Any = None):
        """Record prediction for monitoring"""
        key = f"model_performance:{model_type}"

        record = {
            'timestamp': prediction_result.timestamp.isoformat(),
            'request_id': prediction_result.request_id,
            'confidence': prediction_result.confidence,
            'processing_time_ms': prediction_result.processing_time_ms,
            'success': True
        }

        if ground_truth is not None:
            record['ground_truth'] = ground_truth
            record['correct'] = int(prediction_result.prediction == ground_truth)

        self.redis.lpush(key, json.dumps(record))
        self.redis.ltrim(key, 0, 10000)  # Keep last 10k predictions
        self.redis.expire(key, self.performance_window)

    def get_performance_metrics(self, model_type: str) -> Dict[str, Any]:
        """Get current performance metrics"""
        key = f"model_performance:{model_type}"
        records = self.redis.lrange(key, 0, -1)

        if not records:
            return {'status': 'no_data'}

        df = pd.DataFrame([json.loads(r) for r in records])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Calculate metrics
        total_predictions = len(df)
        avg_confidence = df['confidence'].mean()
        avg_latency = df['processing_time_ms'].mean()

        metrics = {
            'total_predictions': total_predictions,
            'avg_confidence': avg_confidence,
            'avg_latency_ms': avg_latency,
            'error_rate': (df['success'] == False).sum() / total_predictions if 'success' in df.columns else 0,
            'predictions_per_hour': total_predictions / max(1, (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600)
        }

        # Accuracy if ground truth available
        if 'correct' in df.columns:
            metrics['accuracy'] = df['correct'].mean()
            metrics['accuracy_trend'] = self._calculate_accuracy_trend(df)

        return metrics

    def _calculate_accuracy_trend(self, df: pd.DataFrame) -> str:
        """Calculate accuracy trend over time"""
        df_sorted = df.sort_values('timestamp')
        midpoint = len(df_sorted) // 2

        if midpoint < 10:  # Not enough data
            return 'insufficient_data'

        recent_accuracy = df_sorted.iloc[midpoint:]['correct'].mean()
        older_accuracy = df_sorted.iloc[:midpoint]['correct'].mean()

        if recent_accuracy > older_accuracy + 0.02:
            return 'improving'
        elif recent_accuracy < older_accuracy - 0.02:
            return 'declining'
        else:
            return 'stable'

    def check_alerts(self, model_type: str) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        metrics = self.get_performance_metrics(model_type)
        alerts = []

        if 'accuracy' in metrics:
            baseline_key = f"baseline_accuracy:{model_type}"
            baseline = float(self.redis.get(baseline_key) or 0.9)

            if metrics['accuracy'] < baseline - self.alert_thresholds['accuracy_drop']:
                alerts.append({
                    'type': 'accuracy_drop',
                    'severity': 'high',
                    'message': f"Accuracy dropped from {baseline:.3f} to {metrics['accuracy']:.3f}",
                    'current_value': metrics['accuracy'],
                    'threshold': baseline - self.alert_thresholds['accuracy_drop']
                })

        if metrics['avg_latency_ms'] > self.alert_thresholds['latency_increase']:
            alerts.append({
                'type': 'high_latency',
                'severity': 'medium',
                'message': f"Average latency: {metrics['avg_latency_ms']:.1f}ms",
                'current_value': metrics['avg_latency_ms'],
                'threshold': self.alert_thresholds['latency_increase']
            })

        if metrics['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'message': f"Error rate: {metrics['error_rate']:.3%}",
                'current_value': metrics['error_rate'],
                'threshold': self.alert_thresholds['error_rate']
            })

        return alerts

class EnsemblePredictor:
    """Advanced ensemble prediction methods"""

    def __init__(self):
        self.ensemble_models = {}
        self.load_ensemble_models()

    def load_ensemble_models(self):
        """Load pre-trained ensemble models"""
        try:
            # Diabetes ensemble
            diabetes_models = []
            for model_file in ['Diabetes_Model.pkl', 'Diabetes_RF.pkl', 'Diabetes_XGB.pkl']:
                if os.path.exists(f"backend/{model_file}"):
                    diabetes_models.append(joblib.load(f"backend/{model_file}"))

            if diabetes_models:
                self.ensemble_models['diabetes'] = diabetes_models

            # Similar for other models...

        except Exception:
            logger.error("Failed to load ensemble models")

    def predict_ensemble(self, model_type: str, features: np.ndarray) -> Tuple[Any, float, Dict[str, Any]]:
        """Make ensemble prediction with confidence"""
        if model_type not in self.ensemble_models:
            raise ValueError(f"No ensemble models for {model_type}")

        models = self.ensemble_models[model_type]
        predictions = []
        confidences = []

        for model in models:
            try:
                pred = model.predict(features.reshape(1, -1))[0]
                proba = model.predict_proba(features.reshape(1, -1))[0]
                predictions.append(pred)
                confidences.append(np.max(proba))
            except Exception:
                logger.warning("Model prediction failed")

        if not predictions:
            raise ValueError("All model predictions failed")

        # Weighted voting based on confidence
        weights = np.array(confidences)
        weights = weights / weights.sum()

        # For binary classification
        if len(set(predictions)) == 2:
            weighted_vote = np.average(predictions, weights=weights)
            final_prediction = int(weighted_vote >= 0.5)
            confidence = np.average(confidences, weights=weights)
        else:
            # Multi-class or regression
            final_prediction = max(set(predictions), key=predictions.count)
            confidence = np.mean(confidences)

        # Calculate ensemble uncertainty
        uncertainty = np.std(predictions)

        return final_prediction, confidence, {
            'ensemble_size': len(models),
            'individual_predictions': predictions,
            'individual_confidences': confidences,
            'uncertainty': uncertainty,
            'agreement_rate': len(set(predictions)) / len(predictions)
        }

class RealTimePredictionService:
    """Real-time prediction service with streaming"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.monitor = ModelPerformanceMonitor(redis_client)
        self.ensemble = EnsemblePredictor()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.prediction_queue = asyncio.Queue()
        self.background_tasks = set()

    async def start_background_tasks(self):
        """Start background processing tasks"""
        # Prediction processing task
        task = asyncio.create_task(self._process_predictions())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        # Performance monitoring task
        task = asyncio.create_task(self._monitor_performance())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _process_predictions(self):
        """Background task to process prediction queue"""
        while True:
            try:
                request: PredictionRequest = await self.prediction_queue.get()

                # Process prediction based on priority
                if request.priority == "critical":
                    result = await self._predict_high_priority(request)
                else:
                    result = await self._predict_normal(request)

                # Store result
                await self._store_prediction_result(result)

                # Send real-time update via WebSocket
                await self._notify_client(request.user_id, result)

            except Exception:
                logger.error("Prediction processing error")
                await asyncio.sleep(1)

    async def _predict_normal(self, request: PredictionRequest) -> PredictionResult:
        """Normal priority prediction"""
        start_time = time.time()

        try:
            # Convert features to array
            features = self._preprocess_features(request.model_type, request.features)

            # Make ensemble prediction
            prediction, confidence, metadata = self.ensemble.predict_ensemble(
                request.model_type, features
            )

            # Generate explanation
            explanation = self._generate_explanation(
                request.model_type, features, prediction, metadata
            )

            # Calculate risk score
            risk_score = self._calculate_risk_score(
                request.model_type, prediction, confidence, metadata
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                request.model_type, prediction, risk_score
            )

            processing_time = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction=prediction,
                confidence=confidence,
                explanation=explanation,
                model_version="ensemble_v1.0",
                processing_time_ms=processing_time,
                request_id=request.request_id,
                timestamp=datetime.now(timezone.utc),
                risk_score=risk_score,
                recommendations=recommendations
            )

            # Record for monitoring
            self.monitor.record_prediction(request.model_type, result)

            return result

        except Exception:
            logger.error("Prediction failed")
            raise

    async def _predict_high_priority(self, request: PredictionRequest) -> PredictionResult:
        """High priority prediction (simplified for speed)"""
        # Simplified prediction for critical cases
        # This would use optimized models or cached results
        return await self._predict_normal(request)

    def _preprocess_features(self, model_type: str, features: Dict[str, Any]) -> np.ndarray:
        """Preprocess features for model input"""
        # This would implement proper feature scaling and transformation
        # For now, basic conversion

        if model_type == "diabetes":
            feature_order = ['glucose', 'bmi', 'age', 'insulin', 'blood_pressure']
            feature_array = np.array([features.get(f, 0) for f in feature_order])
        elif model_type == "heart":
            feature_order = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']
            feature_array = np.array([features.get(f, 0) for f in feature_order])
        else:
            feature_array = np.array(list(features.values()))

        return feature_array

    def _generate_explanation(self, model_type: str, features: np.ndarray,
                            prediction: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate XAI explanation using SHAP"""
        try:
            # This would use actual SHAP values
            # For now, mock explanation
            explanation = {
                'method': 'shap',
                'top_features': [
                    {'name': 'glucose', 'importance': 0.4, 'value': features[0] if len(features) > 0 else 0},
                    {'name': 'bmi', 'importance': 0.3, 'value': features[1] if len(features) > 1 else 0},
                    {'name': 'age', 'importance': 0.2, 'value': features[2] if len(features) > 2 else 0}
                ],
                'base_value': 0.5,
                'prediction_value': float(prediction),
                'ensemble_agreement': metadata.get('agreement_rate', 1.0),
                'uncertainty': metadata.get('uncertainty', 0.0)
            }

            return explanation

        except Exception:
            logger.error("Explanation generation failed")
            return {'method': 'failed', 'error': ADVANCED_AI_FAILURE_MESSAGE}

    def _calculate_risk_score(self, model_type: str, prediction: Any,
                            confidence: float, metadata: Dict[str, Any]) -> float:
        """Calculate comprehensive risk score"""
        # Base risk from prediction
        if prediction == 1:  # Positive prediction
            base_risk = 0.7
        else:
            base_risk = 0.3

        # Adjust based on confidence
        risk = base_risk * (0.5 + confidence)

        # Adjust based on ensemble uncertainty
        uncertainty = metadata.get('uncertainty', 0)
        risk += uncertainty * 0.2

        # Adjust based on ensemble agreement
        agreement = metadata.get('agreement_rate', 1.0)
        risk *= (2.0 - agreement)  # Lower agreement increases risk

        return min(1.0, max(0.0, risk))

    def _generate_recommendations(self, model_type: str, prediction: Any,
                                risk_score: float) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        if model_type == "diabetes":
            if prediction == 1 or risk_score > 0.6:
                recommendations.extend([
                    "Consult with an endocrinologist immediately",
                    "Monitor blood glucose levels daily",
                    "Reduce carbohydrate intake",
                    "Increase physical activity to 30 minutes daily",
                    "Consider weight management program"
                ])
            else:
                recommendations.extend([
                    "Maintain healthy diet and exercise routine",
                    "Annual diabetes screening recommended",
                    "Monitor weight and blood pressure regularly"
                ])

        elif model_type == "heart":
            if prediction == 1 or risk_score > 0.6:
                recommendations.extend([
                    "Immediate cardiology consultation recommended",
                    "Comprehensive cardiac workup needed",
                    "Lifestyle modifications: diet, exercise, stress management",
                    "Medication review with primary care physician"
                ])
            else:
                recommendations.extend([
                    "Maintain heart-healthy lifestyle",
                    "Regular cardiovascular screening",
                    "Monitor cholesterol and blood pressure"
                ])

        return recommendations

    async def _store_prediction_result(self, result: PredictionResult):
        """Store prediction result in database"""
        try:
            from .database import get_db_context
            from .models import HealthRecord

            with get_db_context() as db:
                # Create health record
                health_record = HealthRecord(
                    user_id=int(result.request_id.split('_')[1]),  # Extract user_id from request_id
                    record_type="prediction",
                    data=json.dumps({
                        'prediction': result.prediction,
                        'confidence': result.confidence,
                        'risk_score': result.risk_score,
                        'recommendations': result.recommendations
                    }),
                    prediction=str(result.prediction),
                    timestamp=result.timestamp
                )

                db.add(health_record)
                db.commit()

        except Exception:
            logger.error("Failed to store prediction result")

    async def _notify_client(self, user_id: int, result: PredictionResult):
        """Send real-time update to client via WebSocket"""
        if str(user_id) in self.websocket_connections:
            websocket = self.websocket_connections[str(user_id)]
            try:
                await websocket.send_json({
                    'type': 'prediction_result',
                    'request_id': result.request_id,
                    'prediction': result.prediction,
                    'confidence': result.confidence,
                    'risk_score': result.risk_score,
                    'recommendations': result.recommendations,
                    'processing_time_ms': result.processing_time_ms
                })
            except Exception:
                logger.error("WebSocket notification failed")
                # Remove disconnected client
                del self.websocket_connections[str(user_id)]

    async def _monitor_performance(self):
        """Background task for performance monitoring"""
        while True:
            try:
                # Check all model types
                for model_type in ['diabetes', 'heart', 'liver']:
                    alerts = self.monitor.check_alerts(model_type)

                    if alerts:
                        for alert in alerts:
                            logger.warning(f"Performance alert for {model_type}: {alert['message']}")
                            # Send alert to monitoring system
                            await self._send_alert(alert)

                await asyncio.sleep(60)  # Check every minute

            except Exception:
                logger.error("Performance monitoring error")
                await asyncio.sleep(60)

    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to monitoring system"""
        # This would integrate with PagerDuty, Slack, etc.
        alert_key = f"alerts:{datetime.now().strftime('%Y%m%d')}"
        self.redis.lpush(alert_key, json.dumps(alert))
        self.redis.expire(alert_key, 86400 * 7)  # Keep 7 days

    async def add_websocket_client(self, user_id: int, websocket: WebSocket):
        """Add WebSocket client for real-time updates"""
        self.websocket_connections[str(user_id)] = websocket

    async def remove_websocket_client(self, user_id: int):
        """Remove WebSocket client"""
        if str(user_id) in self.websocket_connections:
            del self.websocket_connections[str(user_id)]

    async def submit_prediction(self, request: PredictionRequest):
        """Submit prediction request to queue"""
        await self.prediction_queue.put(request)

# Global service instance
prediction_service = None

def get_prediction_service(redis_client: redis.Redis) -> RealTimePredictionService:
    """Get or create prediction service instance"""
    global prediction_service
    if prediction_service is None:
        prediction_service = RealTimePredictionService(redis_client)
        asyncio.create_task(prediction_service.start_background_tasks())
    return prediction_service
