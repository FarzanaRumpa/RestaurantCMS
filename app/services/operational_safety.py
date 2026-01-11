"""
Operational Safety & Guardrails
===============================
Infrastructure for rate limiting, circuit breakers, and feature flags.

Features:
1. Per-restaurant rate limiting
2. Circuit breakers for external services
3. Feature flags for safe rollouts
4. Fail-safe behaviors
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
import threading
import time
import logging
from typing import Optional, Callable, Dict
from enum import Enum

from app import db

logger = logging.getLogger(__name__)


# =============================================================================
# FEATURE FLAGS
# =============================================================================

class FeatureFlagModel(db.Model):
    """
    Feature flags for controlled rollouts.

    Supports:
    - Global flags (all tenants)
    - Restaurant-specific flags
    - Percentage rollouts
    - Time-based activation
    """
    __tablename__ = 'feature_flags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)

    # Flag type
    flag_type = db.Column(db.String(20), default='boolean')  # boolean, percentage, list

    # Global settings
    is_enabled = db.Column(db.Boolean, default=False)
    percentage = db.Column(db.Integer, default=0)  # 0-100 for percentage rollouts

    # Restaurant whitelist/blacklist
    enabled_restaurants = db.Column(db.Text, nullable=True)  # JSON array of restaurant IDs
    disabled_restaurants = db.Column(db.Text, nullable=True)  # JSON array of restaurant IDs

    # Time-based activation
    activate_at = db.Column(db.DateTime, nullable=True)
    deactivate_at = db.Column(db.DateTime, nullable=True)

    # Metadata
    category = db.Column(db.String(50), nullable=True)  # billing, ordering, webhooks, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'percentage': self.percentage,
            'category': self.category,
            'activate_at': self.activate_at.isoformat() if self.activate_at else None,
            'deactivate_at': self.deactivate_at.isoformat() if self.deactivate_at else None
        }


class FeatureFlags:
    """
    Feature flag service for controlled feature rollouts.
    """

    # Known feature flags
    BILLING_ENABLED = 'billing_enabled'
    WEBHOOKS_ENABLED = 'webhooks_enabled'
    NEW_CHECKOUT = 'new_checkout'
    ADVANCED_ANALYTICS = 'advanced_analytics_v2'
    WHITE_LABEL = 'white_label'
    API_V2 = 'api_v2'

    # In-memory cache
    _cache = {}
    _cache_ttl = 60  # seconds
    _cache_lock = threading.Lock()

    @classmethod
    def is_enabled(cls, flag_name: str, restaurant_id: int = None) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            restaurant_id: Optional restaurant ID for tenant-specific flags

        Returns:
            True if feature is enabled
        """
        # Check cache first
        cache_key = f"{flag_name}:{restaurant_id or 'global'}"
        cached = cls._get_cached(cache_key)
        if cached is not None:
            return cached

        # Query database
        flag = FeatureFlagModel.query.filter_by(name=flag_name).first()
        if not flag:
            return False

        result = cls._evaluate_flag(flag, restaurant_id)
        cls._set_cached(cache_key, result)
        return result

    @classmethod
    def _evaluate_flag(cls, flag: FeatureFlagModel, restaurant_id: int = None) -> bool:
        """Evaluate a feature flag"""
        now = datetime.utcnow()

        # Check time-based activation
        if flag.activate_at and now < flag.activate_at:
            return False
        if flag.deactivate_at and now > flag.deactivate_at:
            return False

        # Check restaurant whitelist/blacklist
        if restaurant_id:
            import json
            if flag.disabled_restaurants:
                try:
                    disabled = json.loads(flag.disabled_restaurants)
                    if restaurant_id in disabled:
                        return False
                except:
                    pass

            if flag.enabled_restaurants:
                try:
                    enabled = json.loads(flag.enabled_restaurants)
                    if restaurant_id in enabled:
                        return True
                except:
                    pass

        # Check percentage rollout
        if flag.flag_type == 'percentage' and flag.percentage > 0:
            if restaurant_id:
                # Consistent hashing based on restaurant ID
                hash_value = hash(f"{flag.name}:{restaurant_id}") % 100
                return hash_value < flag.percentage
            return False

        return flag.is_enabled

    @classmethod
    def _get_cached(cls, key: str):
        with cls._cache_lock:
            if key in cls._cache:
                value, timestamp = cls._cache[key]
                if time.time() - timestamp < cls._cache_ttl:
                    return value
        return None

    @classmethod
    def _set_cached(cls, key: str, value: bool):
        with cls._cache_lock:
            cls._cache[key] = (value, time.time())

    @classmethod
    def clear_cache(cls):
        """Clear the feature flag cache"""
        with cls._cache_lock:
            cls._cache = {}


def feature_flag_required(flag_name: str, fallback=None):
    """
    Decorator to gate a function behind a feature flag.

    Args:
        flag_name: Name of the feature flag
        fallback: Optional fallback return value if flag is disabled
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            restaurant_id = getattr(g, 'restaurant_id', None)
            if not FeatureFlags.is_enabled(flag_name, restaurant_id):
                if fallback is not None:
                    return fallback
                return jsonify({
                    'error': {
                        'code': 'FEATURE_DISABLED',
                        'message': f'Feature {flag_name} is not enabled'
                    }
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitState(Enum):
    CLOSED = 'closed'  # Normal operation
    OPEN = 'open'      # Failing, reject requests
    HALF_OPEN = 'half_open'  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures when external services are down.
    """

    _breakers: Dict[str, 'CircuitBreaker'] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self._lock = threading.Lock()

    @classmethod
    def get(cls, name: str, **kwargs) -> 'CircuitBreaker':
        """Get or create a circuit breaker by name"""
        with cls._lock:
            if name not in cls._breakers:
                cls._breakers[name] = cls(name, **kwargs)
            return cls._breakers[name]

    def call(self, func: Callable, *args, **kwargs):
        """Execute a function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    raise CircuitOpenError(f"Circuit {self.name} is open")

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(f"Circuit {self.name} half-open limit reached")
                self.half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def _record_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self._close()
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def _record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._open()
            elif self.failure_count >= self.failure_threshold:
                self._open()

    def _open(self):
        self.state = CircuitState.OPEN
        logger.warning(f"Circuit breaker {self.name} opened")

    def _close(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker {self.name} closed")

    def get_status(self) -> Dict:
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'last_failure': self.last_failure_time
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Circuit breakers for external services
PAYMENT_CIRCUIT = 'payment_provider'
SMS_CIRCUIT = 'sms_provider'
EMAIL_CIRCUIT = 'email_provider'


def with_circuit_breaker(circuit_name: str, fallback=None):
    """
    Decorator to wrap function with circuit breaker.

    Args:
        circuit_name: Name of the circuit breaker
        fallback: Optional fallback function or value
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            circuit = CircuitBreaker.get(circuit_name)
            try:
                return circuit.call(f, *args, **kwargs)
            except CircuitOpenError:
                if fallback is not None:
                    if callable(fallback):
                        return fallback(*args, **kwargs)
                    return fallback
                raise
        return decorated_function
    return decorator


# =============================================================================
# RATE LIMITING ENHANCEMENTS
# =============================================================================

class RestaurantRateLimiter:
    """
    Per-restaurant rate limiting.

    Different limits for different operations:
    - Orders: Higher limits during peak hours
    - API calls: Based on plan
    - Admin operations: Lower limits
    """

    DEFAULT_LIMITS = {
        'order_create': (100, 60),      # 100 per minute
        'menu_update': (30, 60),        # 30 per minute
        'api_call': (1000, 3600),       # 1000 per hour
        'export': (5, 3600),            # 5 per hour
        'webhook': (100, 60),           # 100 per minute
    }

    PLAN_MULTIPLIERS = {
        'free': 0.5,
        'starter': 1.0,
        'professional': 2.0,
        'enterprise': 5.0
    }

    _limits = {}
    _lock = threading.Lock()

    @classmethod
    def check_limit(cls, restaurant_id: int, operation: str, plan: str = 'starter') -> tuple:
        """
        Check if operation is within rate limits.

        Returns:
            Tuple of (allowed: bool, remaining: int, reset_at: datetime)
        """
        limit, window = cls.DEFAULT_LIMITS.get(operation, (100, 60))
        multiplier = cls.PLAN_MULTIPLIERS.get(plan, 1.0)
        limit = int(limit * multiplier)

        key = f"{restaurant_id}:{operation}"
        now = time.time()

        with cls._lock:
            if key not in cls._limits:
                cls._limits[key] = {'count': 0, 'window_start': now}

            entry = cls._limits[key]

            # Reset if window expired
            if now - entry['window_start'] > window:
                entry['count'] = 0
                entry['window_start'] = now

            remaining = limit - entry['count']
            reset_at = datetime.utcfromtimestamp(entry['window_start'] + window)

            if entry['count'] >= limit:
                return False, 0, reset_at

            entry['count'] += 1
            return True, remaining - 1, reset_at


def restaurant_rate_limit(operation: str):
    """
    Decorator for per-restaurant rate limiting.

    Args:
        operation: Operation type (order_create, menu_update, etc.)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            restaurant_id = getattr(g, 'restaurant_id', None)
            plan = getattr(g, 'restaurant_plan', 'starter')

            if restaurant_id:
                allowed, remaining, reset_at = RestaurantRateLimiter.check_limit(
                    restaurant_id, operation, plan
                )

                if not allowed:
                    response = jsonify({
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': 'Rate limit exceeded for this operation',
                            'retry_after': int((reset_at - datetime.utcnow()).total_seconds())
                        }
                    })
                    response.status_code = 429
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = reset_at.isoformat()
                    return response

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# FAIL-SAFE BEHAVIORS
# =============================================================================

class FailSafe:
    """
    Fail-safe behaviors for critical operations.
    """

    @staticmethod
    def ordering_fallback(restaurant_id: int) -> bool:
        """
        Check if ordering should continue despite payment provider outage.

        Returns True if ordering should be allowed (cash/offline mode).
        """
        # Check payment provider circuit
        payment_circuit = CircuitBreaker.get(PAYMENT_CIRCUIT)

        if payment_circuit.state == CircuitState.OPEN:
            # Allow ordering but disable online payments
            return True

        return True

    @staticmethod
    def webhook_dedup_check(webhook_id: str) -> bool:
        """
        Check if webhook should be processed (avoid duplicates).

        Returns True if webhook should be processed.
        """
        from app.models.background_job_models import IdempotencyRecord

        existing = IdempotencyRecord.query.filter_by(
            idempotency_key=f"webhook:{webhook_id}"
        ).first()

        return existing is None

    @staticmethod
    def graceful_degradation(service: str) -> Dict:
        """
        Get degradation mode for a service.

        Returns configuration for degraded operation.
        """
        degradation_modes = {
            'payment': {
                'allow_cash_orders': True,
                'allow_online_payments': False,
                'message': 'Online payments temporarily unavailable'
            },
            'notifications': {
                'skip_sms': True,
                'skip_email': False,
                'message': 'Some notifications may be delayed'
            },
            'analytics': {
                'use_cached_data': True,
                'max_age_hours': 24,
                'message': 'Analytics may show older data'
            }
        }

        return degradation_modes.get(service, {})

