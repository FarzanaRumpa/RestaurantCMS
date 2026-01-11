"""
Tenant Routing Middleware
=========================
Middleware for routing requests to correct tenant based on domain.

Features:
1. Custom domain detection
2. Subdomain parsing
3. Tenant context setup
"""

from flask import request, g
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware for multi-tenant domain routing.

    Detects custom domains and sets up tenant context.
    """

    def __init__(self, app=None):
        self.app = app
        self.saas_domain = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.saas_domain = app.config.get('SAAS_DOMAIN', 'localhost')
        app.before_request(self._resolve_tenant)

    def _resolve_tenant(self):
        """Resolve tenant from request domain"""
        host = request.host.lower()

        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]

        # Check if this is a custom domain
        if not self._is_saas_domain(host):
            restaurant_id = self._get_restaurant_by_domain(host)
            if restaurant_id:
                g.tenant_id = restaurant_id
                g.is_custom_domain = True
                g.custom_domain = host
                logger.debug(f"Custom domain resolved: {host} -> Restaurant {restaurant_id}")
                return

        # Check for subdomain on SaaS domain
        subdomain = self._extract_subdomain(host)
        if subdomain:
            restaurant_id = self._get_restaurant_by_subdomain(subdomain)
            if restaurant_id:
                g.tenant_id = restaurant_id
                g.is_custom_domain = False
                g.subdomain = subdomain
                logger.debug(f"Subdomain resolved: {subdomain} -> Restaurant {restaurant_id}")
                return

        # No tenant context
        g.tenant_id = None
        g.is_custom_domain = False

    def _is_saas_domain(self, host):
        """Check if host is the main SaaS domain"""
        saas_domains = [
            self.saas_domain,
            'localhost',
            '127.0.0.1'
        ]
        return any(host == d or host.endswith(f'.{d}') for d in saas_domains)

    def _extract_subdomain(self, host):
        """Extract subdomain from host"""
        parts = host.split('.')

        # Handle localhost
        if 'localhost' in host or '127.0.0.1' in host:
            return None

        # Need at least 3 parts for subdomain (e.g., sub.example.com)
        if len(parts) >= 3:
            return parts[0]

        return None

    def _get_restaurant_by_domain(self, domain):
        """Get restaurant ID by custom domain"""
        from app.services.white_label_service import WhiteLabelService
        return WhiteLabelService.get_tenant_by_domain(domain)

    def _get_restaurant_by_subdomain(self, subdomain):
        """Get restaurant ID by subdomain"""
        from app.models import Restaurant
        restaurant = Restaurant.query.filter_by(
            public_id=subdomain,
            is_active=True
        ).first()
        return restaurant.id if restaurant else None


def tenant_context_required(f):
    """
    Decorator to require tenant context.

    Use on routes that must have a resolved tenant.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'tenant_id', None):
            from flask import jsonify
            return jsonify({
                'error': 'Tenant context required'
            }), 404
        return f(*args, **kwargs)
    return decorated_function


def get_current_tenant_id():
    """Get the current tenant (restaurant) ID from context"""
    return getattr(g, 'tenant_id', None)


def is_custom_domain():
    """Check if request is from a custom domain"""
    return getattr(g, 'is_custom_domain', False)

