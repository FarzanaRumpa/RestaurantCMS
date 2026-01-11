"""
API Module
==========
Versioned API infrastructure and endpoints.
"""

from app.api.versioning import (
    API_VERSION_1,
    API_VERSION_2,
    CURRENT_API_VERSION,
    SUPPORTED_VERSIONS,
    APIError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ConflictError,
    ServiceUnavailableError,
    PaginatedResponse,
    api_version,
    api_response,
    before_request_handler,
    after_request_handler,
    register_error_handlers
)

