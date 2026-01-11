"""
API Versioning & Developer Experience
=====================================
Infrastructure for versioned APIs and developer tools.

Features:
1. API versioning with backward compatibility
2. Standardized error responses
3. Consistent pagination
4. Rate limit headers
5. Request correlation IDs
"""

from datetime import datetime
from functools import wraps
from flask import request, jsonify, g, current_app
import uuid
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# API VERSION CONSTANTS
# =============================================================================

API_VERSION_1 = 'v1'
API_VERSION_2 = 'v2'
CURRENT_API_VERSION = API_VERSION_1
SUPPORTED_VERSIONS = [API_VERSION_1]


# =============================================================================
# STANDARDIZED ERROR SCHEMA
# =============================================================================

class APIError(Exception):
    """Base API Error with standardized response format"""

    def __init__(self, message: str, code: str = None, status_code: int = 400,
                 details: dict = None, field: str = None):
        self.message = message
        self.code = code or 'BAD_REQUEST'
        self.status_code = status_code
        self.details = details or {}
        self.field = field
        super().__init__(self.message)

    def to_dict(self):
        error_dict = {
            'error': {
                'code': self.code,
                'message': self.message,
                'status': self.status_code,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': getattr(g, 'correlation_id', None)
            }
        }
        if self.field:
            error_dict['error']['field'] = self.field
        if self.details:
            error_dict['error']['details'] = self.details
        return error_dict


class ValidationError(APIError):
    """Validation error for invalid input"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            status_code=400,
            field=field,
            details=details
        )


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with ID '{identifier}' not found"
        super().__init__(
            message=message,
            code='NOT_FOUND',
            status_code=404
        )


class AuthenticationError(APIError):
    """Authentication required error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code='AUTHENTICATION_REQUIRED',
            status_code=401
        )


class AuthorizationError(APIError):
    """Insufficient permissions error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code='FORBIDDEN',
            status_code=403
        )


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details={'retry_after': retry_after}
        )


class ConflictError(APIError):
    """Resource conflict error"""
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            code='CONFLICT',
            status_code=409,
            details={'resource': resource} if resource else None
        )


class ServiceUnavailableError(APIError):
    """Service temporarily unavailable"""
    def __init__(self, message: str = "Service temporarily unavailable", retry_after: int = None):
        details = {'retry_after': retry_after} if retry_after else None
        super().__init__(
            message=message,
            code='SERVICE_UNAVAILABLE',
            status_code=503,
            details=details
        )


# =============================================================================
# PAGINATION HELPER
# =============================================================================

class PaginatedResponse:
    """Standardized pagination for list endpoints"""

    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = None, serialize_fn=None):
        """
        Paginate a SQLAlchemy query and return standardized response.

        Args:
            query: SQLAlchemy query object
            page: Page number (1-based)
            per_page: Items per page
            serialize_fn: Function to serialize each item

        Returns:
            Dict with data and pagination metadata
        """
        per_page = min(
            per_page or PaginatedResponse.DEFAULT_PAGE_SIZE,
            PaginatedResponse.MAX_PAGE_SIZE
        )
        page = max(1, page)

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        items = pagination.items
        if serialize_fn:
            items = [serialize_fn(item) for item in items]
        elif hasattr(items[0] if items else None, 'to_dict'):
            items = [item.to_dict() for item in items]

        return {
            'data': items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': pagination.next_num if pagination.has_next else None,
                'prev_page': pagination.prev_num if pagination.has_prev else None
            }
        }

    @staticmethod
    def get_pagination_params():
        """Extract pagination parameters from request"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', PaginatedResponse.DEFAULT_PAGE_SIZE))
        except (ValueError, TypeError):
            page = 1
            per_page = PaginatedResponse.DEFAULT_PAGE_SIZE

        return page, min(per_page, PaginatedResponse.MAX_PAGE_SIZE)


# =============================================================================
# REQUEST CORRELATION
# =============================================================================

def generate_correlation_id():
    """Generate a unique correlation ID for request tracking"""
    return f"req_{uuid.uuid4().hex[:16]}"


def before_request_handler():
    """Set up correlation ID and timing for each request"""
    # Get or generate correlation ID
    g.correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()
    g.request_start_time = datetime.utcnow()

    # Log incoming request
    logger.info(
        f"[{g.correlation_id}] {request.method} {request.path}",
        extra={
            'correlation_id': g.correlation_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        }
    )


def after_request_handler(response):
    """Add standard headers to all responses"""
    # Add correlation ID to response
    response.headers['X-Correlation-ID'] = getattr(g, 'correlation_id', 'unknown')

    # Add rate limit headers (if available from limiter)
    if hasattr(g, 'view_rate_limit'):
        response.headers['X-RateLimit-Limit'] = g.view_rate_limit.limit
        response.headers['X-RateLimit-Remaining'] = g.view_rate_limit.remaining
        response.headers['X-RateLimit-Reset'] = g.view_rate_limit.reset

    # Add timing header
    if hasattr(g, 'request_start_time'):
        duration = (datetime.utcnow() - g.request_start_time).total_seconds()
        response.headers['X-Response-Time'] = f"{duration:.3f}s"

    # Add API version header
    response.headers['X-API-Version'] = CURRENT_API_VERSION

    return response


# =============================================================================
# API VERSION DECORATOR
# =============================================================================

def api_version(version: str = API_VERSION_1, deprecated: bool = False):
    """
    Decorator to mark API endpoints with version.

    Args:
        version: API version this endpoint belongs to
        deprecated: Whether this endpoint is deprecated
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if version is supported
            if version not in SUPPORTED_VERSIONS:
                return jsonify({
                    'error': {
                        'code': 'UNSUPPORTED_VERSION',
                        'message': f"API version '{version}' is not supported",
                        'supported_versions': SUPPORTED_VERSIONS
                    }
                }), 400

            # Add deprecation warning
            response = f(*args, **kwargs)

            if deprecated:
                if isinstance(response, tuple):
                    resp, status = response
                else:
                    resp, status = response, 200

                # If it's a Response object, add header
                if hasattr(resp, 'headers'):
                    resp.headers['X-API-Deprecated'] = 'true'
                    resp.headers['Deprecation'] = 'true'

            return response
        return decorated_function
    return decorator


# =============================================================================
# SUCCESS RESPONSE HELPER
# =============================================================================

def api_response(data=None, message: str = None, status_code: int = 200, meta: dict = None):
    """
    Create a standardized API response.

    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code
        meta: Optional metadata

    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': True,
        'request_id': getattr(g, 'correlation_id', None)
    }

    if data is not None:
        response['data'] = data

    if message:
        response['message'] = message

    if meta:
        response['meta'] = meta

    return jsonify(response), status_code


# =============================================================================
# ERROR HANDLER REGISTRATION
# =============================================================================

def register_error_handlers(app):
    """Register global error handlers for the Flask app"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(error.description) if hasattr(error, 'description') else 'Bad request',
                'status': 400,
                'request_id': getattr(g, 'correlation_id', None)
            }
        }), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found',
                'status': 404,
                'request_id': getattr(g, 'correlation_id', None)
            }
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An internal server error occurred',
                'status': 500,
                'request_id': getattr(g, 'correlation_id', None)
            }
        }), 500

