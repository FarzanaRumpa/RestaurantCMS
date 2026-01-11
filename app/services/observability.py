"""
Observability & Performance Monitoring
======================================
Infrastructure for metrics, structured logging, and performance tracking.

Features:
1. Structured JSON logging
2. Correlation ID tracking
3. Performance metrics
4. Request/Response timing
"""

from datetime import datetime
from functools import wraps
import time
import json
import logging
from flask import g, request
from typing import Dict, Any, Optional
import threading


# =============================================================================
# METRICS COLLECTOR
# =============================================================================

class MetricsCollector:
    """
    In-memory metrics collector for observability.

    In production, this would integrate with Prometheus, DataDog, etc.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._metrics = {
                        'counters': {},
                        'gauges': {},
                        'histograms': {}
                    }
        return cls._instance

    def increment(self, name: str, value: int = 1, labels: Dict = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._metrics['counters'][key] = self._metrics['counters'].get(key, 0) + value

    def gauge(self, name: str, value: float, labels: Dict = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._metrics['gauges'][key] = value

    def histogram(self, name: str, value: float, labels: Dict = None):
        """Record a histogram observation"""
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._metrics['histograms']:
                self._metrics['histograms'][key] = {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'buckets': {}
                }
            hist = self._metrics['histograms'][key]
            hist['count'] += 1
            hist['sum'] += value
            hist['min'] = min(hist['min'], value)
            hist['max'] = max(hist['max'], value)

    def _make_key(self, name: str, labels: Dict = None) -> str:
        """Create a unique key for a metric with labels"""
        if labels:
            label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def get_metrics(self) -> Dict:
        """Get all current metrics"""
        with self._lock:
            return {
                'counters': dict(self._metrics['counters']),
                'gauges': dict(self._metrics['gauges']),
                'histograms': {k: dict(v) for k, v in self._metrics['histograms'].items()}
            }

    def reset(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self._metrics = {'counters': {}, 'gauges': {}, 'histograms': {}}


# Global metrics instance
metrics = MetricsCollector()


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================

class StructuredLogFormatter(logging.Formatter):
    """JSON structured log formatter"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add correlation ID if available
        if hasattr(g, 'correlation_id'):
            log_entry['correlation_id'] = g.correlation_id

        # Add request context if available
        try:
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr
                }
        except RuntimeError:
            pass  # Outside request context

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['data'] = record.extra_data

        # Add exception info
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def configure_structured_logging(app):
    """Configure structured JSON logging for the application"""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredLogFormatter())

    # Set log level from config
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    handler.setLevel(getattr(logging, log_level))

    # Apply to app logger
    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, log_level))

    # Apply to root logger for third-party libraries
    logging.root.handlers = []
    logging.root.addHandler(handler)


# =============================================================================
# PERFORMANCE DECORATORS
# =============================================================================

def track_performance(metric_name: str = None, labels: Dict = None):
    """
    Decorator to track function execution time.

    Args:
        metric_name: Name for the metric (defaults to function name)
        labels: Additional metric labels
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            name = metric_name or f"{f.__module__}.{f.__name__}"
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time

                # Record success
                metrics.histogram(f"{name}_duration_seconds", duration, labels)
                metrics.increment(f"{name}_total", labels={**(labels or {}), 'status': 'success'})

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Record failure
                metrics.histogram(f"{name}_duration_seconds", duration, labels)
                metrics.increment(f"{name}_total", labels={**(labels or {}), 'status': 'error'})

                raise

        return decorated_function
    return decorator


def track_db_query(query_name: str = None):
    """Decorator to track database query performance"""
    return track_performance(f"db_query_{query_name}" if query_name else "db_query")


# =============================================================================
# REQUEST MIDDLEWARE
# =============================================================================

class RequestMetrics:
    """Middleware for tracking request metrics"""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        g.request_start_time = time.time()

    def _after_request(self, response):
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time

            # Record request duration
            labels = {
                'method': request.method,
                'endpoint': request.endpoint or 'unknown',
                'status': str(response.status_code)
            }

            metrics.histogram('http_request_duration_seconds', duration, labels)
            metrics.increment('http_requests_total', labels=labels)

        return response


# =============================================================================
# HEALTH CHECK
# =============================================================================

class HealthCheck:
    """Health check utilities for operational monitoring"""

    @staticmethod
    def check_database() -> Dict:
        """Check database connectivity"""
        from app import db
        from sqlalchemy import text
        try:
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'latency_ms': 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def check_redis() -> Dict:
        """Check Redis connectivity (if used)"""
        # Placeholder for Redis health check
        return {'status': 'not_configured'}

    @staticmethod
    def get_system_health() -> Dict:
        """Get overall system health status"""
        checks = {
            'database': HealthCheck.check_database(),
            'redis': HealthCheck.check_redis()
        }

        overall_status = 'healthy'
        for check in checks.values():
            if check.get('status') == 'unhealthy':
                overall_status = 'unhealthy'
                break

        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': checks,
            'metrics': {
                'uptime_seconds': time.time() - getattr(HealthCheck, '_start_time', time.time())
            }
        }


HealthCheck._start_time = time.time()

