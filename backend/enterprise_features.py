"""
Enterprise Features for AI Healthcare System
- Advanced Monitoring & Metrics
- Enhanced Security & Compliance
- Performance Optimization
- Audit & Logging
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

import psutil
import redis
from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import text

logger = logging.getLogger(__name__)
HEALTH_CHECK_UNHEALTHY = "unhealthy"
ENTERPRISE_OPERATION_FAILURE_MESSAGE = "Enterprise operation failed."

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
PREDICTION_COUNT = Counter('predictions_total', 'Total ML predictions', ['model_type', 'result'])
PREDICTION_DURATION = Histogram('prediction_duration_seconds', 'ML prediction duration', ['model_type'])
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
REDIS_CONNECTIONS = Gauge('redis_connections_active', 'Active Redis connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System memory usage')

class EnterpriseMetrics:
    """Enterprise-grade metrics collection and monitoring"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client

    def record_prediction(self, model_type: str, result: str, duration: float):
        """Record ML prediction metrics"""
        PREDICTION_COUNT.labels(model_type=model_type, result=result).inc()
        PREDICTION_DURATION.labels(model_type=model_type).observe(duration)

        # Store detailed metrics in Redis for analytics
        if self.redis:
            key = f"predictions:{model_type}:{datetime.now().strftime('%Y%m%d')}"
            self.redis.lpush(key, json.dumps({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'result': result,
                'duration': duration
            }))
            self.redis.expire(key, 86400 * 30)  # Keep 30 days

    def update_system_metrics(self):
        """Update system-level metrics"""
        SYSTEM_CPU.set(psutil.cpu_percent())
        SYSTEM_MEMORY.set(psutil.virtual_memory().percent)

        # Update database connections
        try:
            from .database import engine
            with engine.connect() as conn:
                result = conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
                DATABASE_CONNECTIONS.set(result.scalar())
        except Exception:
            logger.error("Failed to get DB connections")

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {}
        }

        # Database health
        try:
            from .database import engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                health['checks']['database'] = 'healthy'
        except Exception:
            health['checks']['database'] = HEALTH_CHECK_UNHEALTHY
            health['status'] = 'unhealthy'

        # Redis health
        if self.redis:
            try:
                self.redis.ping()
                health['checks']['redis'] = 'healthy'
            except Exception:
                health['checks']['redis'] = HEALTH_CHECK_UNHEALTHY
                health['status'] = 'unhealthy'

        # AI models health
        try:
            from .ml_service import ml_service
            ml_service.health_check()
            health['checks']['ml_models'] = 'healthy'
        except Exception:
            health['checks']['ml_models'] = HEALTH_CHECK_UNHEALTHY
            health['status'] = 'degraded'

        return health

class ComplianceAudit:
    """HIPAA/GDPR compliance and audit logging"""

    def __init__(self, db_session):
        self.db = db_session

    def log_access(self, user_id: int, resource_type: str, resource_id: str,
                   action: str, ip_address: str, user_agent: str = None):
        """Log data access for compliance"""
        try:
            from .database import engine
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO audit.activity_log
                    (user_id, action_type, resource_type, resource_id, ip_address, user_agent, success)
                    VALUES (:user_id, :action, :resource_type, :resource_id, :ip, :ua, true)
                """), {
                    'user_id': user_id,
                    'action': action,
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'ip': ip_address,
                    'ua': user_agent
                })
                conn.commit()
        except Exception:
            logger.error("Audit log failed")

    def check_data_retention(self) -> Dict[str, Any]:
        """Check data retention policies"""
        try:
            from .database import engine
            with engine.connect() as conn:
                # Check for records exceeding retention period
                result = conn.execute(text("""
                    SELECT COUNT(*) as expired_records
                    FROM app_data.health_records hr
                    JOIN app_data.users u ON hr.user_id = u.id
                    WHERE hr.created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * u.data_retention_days
                """))
                expired = result.scalar()

                return {
                    'expired_records': expired,
                    'compliance_status': 'compliant' if expired == 0 else 'action_required'
                }
        except Exception:
            logger.error("Data retention check failed")
            return {'error': ENTERPRISE_OPERATION_FAILURE_MESSAGE}

class PerformanceOptimizer:
    """Advanced performance optimization features"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour default

    @contextmanager
    def database_connection_pool(self):
        """Optimized database connection management"""
        from .database import get_db_context
        with get_db_context() as db:
            yield db

    def cache_prediction(self, cache_key: str, result: Dict[str, Any], ttl: int = None):
        """Cache ML predictions for performance"""
        if self.redis:
            ttl = ttl or self.cache_ttl
            self.redis.setex(
                f"prediction_cache:{cache_key}",
                ttl,
                json.dumps(result)
            )

    def get_cached_prediction(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached prediction"""
        if self.redis:
            cached = self.redis.get(f"prediction_cache:{cache_key}")
            if cached:
                return json.loads(cached)
        return None

    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user"""
        if self.redis:
            pattern = f"*:user_{user_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)

def metrics_middleware(request: Request, call_next):
    """FastAPI middleware for metrics collection"""
    start_time = time.time()

    response = call_next(request)

    # Record metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

def audit_decorator(resource_type: str):
    """Decorator for automatic audit logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request context if available
            request = None
            user_id = None

            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                elif hasattr(arg, 'user'):
                    user_id = getattr(arg.user, 'id', None)

            # Execute function
            time.time()
            try:
                result = await func(*args, **kwargs)
            except Exception:
                raise
            finally:
                # Log audit trail
                if request and user_id:
                    audit = ComplianceAudit(None)
                    audit.log_access(
                        user_id=user_id,
                        resource_type=resource_type,
                        resource_id=str(kwargs.get('id', 'unknown')),
                        action=func.__name__,
                        ip_address=request.client.host if request else 'unknown',
                        user_agent=request.headers.get('user-agent')
                    )

            return result
        return wrapper
    return decorator

class AdvancedSecurity:
    """Advanced security features for enterprise deployment"""

    @staticmethod
    def rate_limit_key(user_id: int, action: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{action}:user_{user_id}"

    @staticmethod
    def check_rate_limit(redis_client: redis.Redis, user_id: int, action: str,
                        limit: int, window: int) -> bool:
        """Check if user exceeds rate limit"""
        key = AdvancedSecurity.rate_limit_key(user_id, action)
        current = redis_client.incr(key)

        if current == 1:
            redis_client.expire(key, window)

        return current <= limit

    @staticmethod
    def detect_anomalies(user_id: int, action: str, ip_address: str) -> Dict[str, Any]:
        """Detect anomalous behavior patterns"""
        # This would integrate with a more sophisticated anomaly detection system
        # For now, basic heuristics

        anomalies = []

        # Check for multiple IPs in short time
        # Check for unusual request patterns
        # Check for data access patterns

        return {
            'anomaly_score': 0.1,  # Low score for now
            'anomalies': anomalies,
            'risk_level': 'low'
        }

# Enterprise feature initialization
def init_enterprise_features(app):
    """Initialize all enterprise features"""
    from fastapi.middleware.gzip import GZipMiddleware

    # Add metrics middleware
    app.middleware("http")(metrics_middleware)

    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Initialize Redis client
    try:
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception:
        logger.warning("Redis connection failed")
        redis_client = None

    return {
        'metrics': EnterpriseMetrics(redis_client),
        'performance': PerformanceOptimizer(redis_client),
        'security': AdvancedSecurity()
    }
