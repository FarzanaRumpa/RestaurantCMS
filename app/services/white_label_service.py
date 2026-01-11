"""
White-Label Service
===================
Service layer for white-label and custom domain management.

Features:
1. Domain registration and verification
2. SSL certificate management
3. Tenant routing
4. Branding configuration
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import logging
import uuid

from app import db
from app.models.white_label_models import CustomDomain, WhiteLabelBranding

logger = logging.getLogger(__name__)


class WhiteLabelService:
    """Service for white-label feature management."""

    @staticmethod
    def is_white_label_allowed(restaurant_id: int) -> bool:
        """
        Check if restaurant's plan allows white-label features.

        Args:
            restaurant_id: The restaurant's database ID

        Returns:
            True if white-label is allowed
        """
        from app.models import Restaurant

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return False

        # Check if plan allows white-label
        return restaurant.has_feature('white_label')

    @staticmethod
    def register_custom_domain(
        restaurant_id: int,
        domain: str,
        verification_method: str = 'dns'
    ) -> Tuple[bool, Optional[CustomDomain], Optional[str]]:
        """
        Register a custom domain for a restaurant.

        Args:
            restaurant_id: The restaurant's database ID
            domain: The custom domain to register
            verification_method: dns, file, or cname

        Returns:
            Tuple of (success, CustomDomain, error_message)
        """
        # Check white-label permission
        if not WhiteLabelService.is_white_label_allowed(restaurant_id):
            return False, None, "White-label not available on current plan"

        # Validate domain format
        domain = domain.lower().strip()
        if not WhiteLabelService._validate_domain(domain):
            return False, None, "Invalid domain format"

        # Check if domain already registered
        existing = CustomDomain.query.filter_by(domain=domain).first()
        if existing:
            if existing.restaurant_id == restaurant_id:
                return True, existing, None
            return False, None, "Domain already registered to another tenant"

        # Check if restaurant already has a domain
        current = CustomDomain.query.filter_by(restaurant_id=restaurant_id).first()
        if current:
            # Update existing
            current.domain = domain
            current.verification_method = verification_method
            current.is_verified = False
            current.verification_token = None
            current.status = 'pending'
            current.generate_verification_token()
            db.session.commit()
            return True, current, None

        # Create new domain registration
        custom_domain = CustomDomain(
            restaurant_id=restaurant_id,
            domain=domain,
            verification_method=verification_method,
            status='pending'
        )
        custom_domain.generate_verification_token()

        db.session.add(custom_domain)
        db.session.commit()

        logger.info(f"Custom domain registered: {domain} for restaurant {restaurant_id}")
        return True, custom_domain, None

    @staticmethod
    def _validate_domain(domain: str) -> bool:
        """Validate domain format"""
        import re
        # Basic domain validation
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))

    @staticmethod
    def verify_domain(restaurant_id: int) -> Tuple[bool, Optional[str]]:
        """
        Attempt to verify the domain ownership.

        This checks DNS TXT records or file verification based on method.

        Returns:
            Tuple of (success, error_message)
        """
        custom_domain = CustomDomain.query.filter_by(restaurant_id=restaurant_id).first()
        if not custom_domain:
            return False, "No domain registered"

        if custom_domain.is_verified:
            return True, None

        try:
            if custom_domain.verification_method == 'dns':
                verified = WhiteLabelService._verify_dns(
                    custom_domain.domain,
                    custom_domain.verification_token
                )
            elif custom_domain.verification_method == 'cname':
                verified = WhiteLabelService._verify_cname(custom_domain.domain)
            else:
                verified = False

            if verified:
                custom_domain.is_verified = True
                custom_domain.verified_at = datetime.utcnow()
                custom_domain.status = 'verified'
                db.session.commit()

                # Trigger SSL issuance
                WhiteLabelService.request_ssl_certificate(restaurant_id)

                logger.info(f"Domain verified: {custom_domain.domain}")
                return True, None
            else:
                return False, "Verification failed. Please check DNS records."

        except Exception as e:
            logger.error(f"Domain verification error: {e}")
            return False, str(e)

    @staticmethod
    def _verify_dns(domain: str, token: str) -> bool:
        """Verify domain via DNS TXT record"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_rcms-verify.{domain}", 'TXT')
            for rdata in answers:
                if token in str(rdata):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _verify_cname(domain: str) -> bool:
        """Verify domain via CNAME record"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                # Should point to our domains
                if 'restaurantcms' in str(rdata).lower():
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def request_ssl_certificate(restaurant_id: int) -> Tuple[bool, Optional[str]]:
        """
        Request SSL certificate for verified domain.

        In production, this would integrate with Let's Encrypt or similar.
        """
        custom_domain = CustomDomain.query.filter_by(restaurant_id=restaurant_id).first()
        if not custom_domain or not custom_domain.is_verified:
            return False, "Domain not verified"

        # Placeholder for actual SSL issuance
        # In production: integrate with certbot/Let's Encrypt API
        custom_domain.ssl_enabled = True
        custom_domain.ssl_issued_at = datetime.utcnow()
        custom_domain.ssl_expires_at = datetime.utcnow() + timedelta(days=90)
        custom_domain.ssl_provider = 'letsencrypt'
        custom_domain.status = 'active'
        custom_domain.is_active = True

        db.session.commit()

        logger.info(f"SSL certificate issued for: {custom_domain.domain}")
        return True, None

    @staticmethod
    def get_tenant_by_domain(domain: str) -> Optional[int]:
        """
        Get restaurant ID for a custom domain.

        Used for request routing.

        Args:
            domain: The incoming request domain

        Returns:
            restaurant_id or None
        """
        domain = domain.lower().strip()

        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]

        custom_domain = CustomDomain.query.filter_by(
            domain=domain,
            is_active=True,
            is_verified=True
        ).first()

        if custom_domain:
            return custom_domain.restaurant_id

        return None

    @staticmethod
    def get_branding(restaurant_id: int) -> Optional[WhiteLabelBranding]:
        """Get white-label branding for a restaurant"""
        return WhiteLabelBranding.query.filter_by(
            restaurant_id=restaurant_id,
            is_enabled=True
        ).first()

    @staticmethod
    def update_branding(restaurant_id: int, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Update white-label branding configuration.

        Args:
            restaurant_id: The restaurant's database ID
            **kwargs: Branding fields to update

        Returns:
            Tuple of (success, error_message)
        """
        if not WhiteLabelService.is_white_label_allowed(restaurant_id):
            return False, "White-label not available on current plan"

        branding = WhiteLabelBranding.query.filter_by(restaurant_id=restaurant_id).first()

        if not branding:
            branding = WhiteLabelBranding(restaurant_id=restaurant_id)
            db.session.add(branding)

        # Update allowed fields
        allowed_fields = [
            'is_enabled', 'logo_url', 'logo_dark_url', 'favicon_url',
            'primary_color', 'secondary_color', 'accent_color',
            'heading_font', 'body_font', 'company_name', 'tagline',
            'footer_text', 'copyright_text', 'support_email', 'support_phone',
            'support_url', 'privacy_policy_url', 'terms_of_service_url',
            'hide_powered_by', 'hide_saas_logo', 'hide_saas_links',
            'custom_css', 'custom_head_html'
        ]

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(branding, field, value)

        db.session.commit()
        logger.info(f"Branding updated for restaurant {restaurant_id}")

        return True, None

    @staticmethod
    def get_customer_facing_branding(restaurant_id: int) -> Dict:
        """
        Get branding configuration for customer-facing pages.

        Returns default SaaS branding if white-label not enabled.
        """
        branding = WhiteLabelService.get_branding(restaurant_id)

        if branding and branding.is_enabled:
            return {
                'is_white_label': True,
                'logo_url': branding.logo_url,
                'favicon_url': branding.favicon_url,
                'primary_color': branding.primary_color,
                'secondary_color': branding.secondary_color,
                'company_name': branding.company_name,
                'tagline': branding.tagline,
                'footer_text': branding.footer_text,
                'copyright_text': branding.copyright_text,
                'hide_powered_by': branding.hide_powered_by,
                'support_email': branding.support_email,
                'custom_css': branding.custom_css,
                'css_variables': branding.get_css_variables()
            }

        # Default SaaS branding
        return {
            'is_white_label': False,
            'logo_url': '/static/images/logo.png',
            'favicon_url': '/static/images/favicon.ico',
            'primary_color': '#6366f1',
            'secondary_color': '#1a1a2e',
            'company_name': 'RestaurantCMS',
            'tagline': 'QR Ordering Made Simple',
            'footer_text': None,
            'copyright_text': f'© {datetime.utcnow().year} RestaurantCMS. All rights reserved.',
            'hide_powered_by': False,
            'support_email': 'support@restaurantcms.com',
            'custom_css': None,
            'css_variables': {
                '--brand-primary': '#6366f1',
                '--brand-secondary': '#1a1a2e',
                '--brand-accent': '#6366f1'
            }
        }

    @staticmethod
    def remove_custom_domain(restaurant_id: int) -> bool:
        """Remove custom domain from a restaurant"""
        custom_domain = CustomDomain.query.filter_by(restaurant_id=restaurant_id).first()
        if custom_domain:
            db.session.delete(custom_domain)
            db.session.commit()
            logger.info(f"Custom domain removed for restaurant {restaurant_id}")
            return True
        return False

