"""
Health Check & Metrics Routes
=============================
Endpoints for system health, metrics, and operational monitoring.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from app.services.observability import HealthCheck, metrics

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.

    Returns 200 if system is healthy, 503 if unhealthy.
    """
    health = HealthCheck.get_system_health()

    status_code = 200 if health['status'] == 'healthy' else 503

    return jsonify(health), status_code


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application is running.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the application is ready to serve requests.
    """
    health = HealthCheck.get_system_health()

    if health['checks']['database']['status'] == 'healthy':
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'reason': 'Database unavailable',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Prometheus-compatible metrics endpoint.

    In production, this would be protected and exposed only internally.
    """
    # Check for basic auth or internal network
    # For now, just return metrics
    all_metrics = metrics.get_metrics()

    # Format as Prometheus text format
    output_lines = []

    # Counters
    for key, value in all_metrics['counters'].items():
        output_lines.append(f"# TYPE {key.split('{')[0]} counter")
        output_lines.append(f"{key} {value}")

    # Gauges
    for key, value in all_metrics['gauges'].items():
        output_lines.append(f"# TYPE {key.split('{')[0]} gauge")
        output_lines.append(f"{key} {value}")

    # Histograms
    for key, hist in all_metrics['histograms'].items():
        base_name = key.split('{')[0]
        labels = key[len(base_name):] if '{' in key else ''
        output_lines.append(f"# TYPE {base_name} histogram")
        output_lines.append(f"{base_name}_count{labels} {hist['count']}")
        output_lines.append(f"{base_name}_sum{labels} {hist['sum']}")

    return '\n'.join(output_lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@health_bp.route('/status', methods=['GET'])
def system_status():
    """
    Detailed system status for admin dashboard.
    """
    from app.models import Restaurant, Order, User
    from app.models.background_job_models import BackgroundJob

    # Get basic stats
    try:
        restaurant_count = Restaurant.query.count()
        active_restaurants = Restaurant.query.filter_by(is_active=True).count()
        order_count = Order.query.count()
        user_count = User.query.count()

        # Background jobs
        pending_jobs = BackgroundJob.query.filter_by(status='pending').count()
        failed_jobs = BackgroundJob.query.filter_by(status='failed').count()

        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'stats': {
                'restaurants': {
                    'total': restaurant_count,
                    'active': active_restaurants
                },
                'orders': {
                    'total': order_count
                },
                'users': {
                    'total': user_count
                },
                'background_jobs': {
                    'pending': pending_jobs,
                    'failed': failed_jobs
                }
            },
            'version': '3.0.0',
            'environment': 'development'
        }), 200

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@health_bp.route('/circuit-breakers', methods=['GET'])
def circuit_breaker_status():
    """Get status of all circuit breakers"""
    from app.services.operational_safety import CircuitBreaker

    breakers = {}
    for name, breaker in CircuitBreaker._breakers.items():
        breakers[name] = breaker.get_status()

    return jsonify({
        'circuit_breakers': breakers,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@health_bp.route('/feature-flags', methods=['GET'])
def feature_flag_status():
    """Get status of feature flags (admin only)"""
    from app.services.operational_safety import FeatureFlagModel

    flags = FeatureFlagModel.query.all()

    return jsonify({
        'feature_flags': [flag.to_dict() for flag in flags],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

