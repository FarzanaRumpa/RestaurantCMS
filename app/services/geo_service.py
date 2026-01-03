"""
Geo Location Service
Detects user's country from IP address for tier-based pricing
"""
import requests
from flask import request, session
import logging

logger = logging.getLogger(__name__)

# Free IP geolocation APIs (fallback chain)
GEO_APIS = [
    {
        'url': 'https://ipapi.co/{ip}/json/',
        'country_key': 'country_code'
    },
    {
        'url': 'http://ip-api.com/json/{ip}',
        'country_key': 'countryCode'
    },
    {
        'url': 'https://ipinfo.io/{ip}/json',
        'country_key': 'country'
    }
]

# Cache for IP lookups (in production, use Redis)
_ip_cache = {}


def get_client_ip():
    """Get the client's real IP address"""
    # Check for proxy headers
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, first is client
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    elif request.headers.get('CF-Connecting-IP'):
        # Cloudflare
        ip = request.headers.get('CF-Connecting-IP')
    else:
        ip = request.remote_addr

    # Handle localhost/development
    if ip in ('127.0.0.1', 'localhost', '::1', None):
        return None

    return ip


def get_country_from_ip(ip_address=None):
    """
    Get country code from IP address using free geo APIs
    Returns ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')
    """
    if ip_address is None:
        ip_address = get_client_ip()

    if not ip_address:
        return None

    # Check cache first
    if ip_address in _ip_cache:
        return _ip_cache[ip_address]

    # Try each API in order
    for api in GEO_APIS:
        try:
            url = api['url'].format(ip=ip_address)
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                data = response.json()
                country_code = data.get(api['country_key'])

                if country_code and len(country_code) == 2:
                    # Cache the result
                    _ip_cache[ip_address] = country_code.upper()
                    return country_code.upper()
        except Exception as e:
            logger.warning(f"Geo API {api['url']} failed: {e}")
            continue

    return None


def get_user_country():
    """
    Get user's country from multiple sources (priority order):
    1. User's registered country (stored in session/database)
    2. Session country (previously detected)
    3. IP-based detection
    4. Default to 'US'
    """
    # Check if user has a registered country preference
    user_country = session.get('user_country')
    if user_country:
        return user_country.upper()

    # Check if we already detected and stored in session
    detected_country = session.get('detected_country')
    if detected_country:
        return detected_country.upper()

    # Try IP-based detection
    ip_country = get_country_from_ip()
    if ip_country:
        session['detected_country'] = ip_country
        return ip_country

    # Default to US
    return 'US'


def set_user_country(country_code):
    """Set user's preferred country (overrides IP detection)"""
    if country_code and len(country_code) == 2:
        session['user_country'] = country_code.upper()
        return True
    return False


def get_pricing_tier():
    """Get the pricing tier for the current user"""
    from app.models.website_content_models import PricingPlan
    country = get_user_country()
    return PricingPlan.get_tier_for_country(country)


def get_country_info():
    """Get complete country info for current user"""
    from app.models.website_content_models import PricingPlan

    country_code = get_user_country()
    tier = PricingPlan.get_tier_for_country(country_code)
    country_name = PricingPlan.get_country_name(country_code)

    # Tier descriptions
    tier_info = {
        'tier1': {'name': 'Premium', 'discount': 0},
        'tier2': {'name': 'Standard', 'discount': 20},
        'tier3': {'name': 'Economy', 'discount': 40},
        'tier4': {'name': 'Budget', 'discount': 60}
    }

    return {
        'country_code': country_code,
        'country_name': country_name,
        'tier': tier,
        'tier_name': tier_info.get(tier, {}).get('name', 'Premium'),
        'discount_percent': tier_info.get(tier, {}).get('discount', 0),
        'is_detected': session.get('detected_country') == country_code,
        'is_manual': session.get('user_country') == country_code
    }


def get_all_countries_for_selector():
    """Get all countries for dropdown selector, grouped by tier"""
    from app.models.website_content_models import PricingPlan

    all_countries = []
    tier_order = ['tier1', 'tier2', 'tier3', 'tier4']

    for tier in tier_order:
        countries = PricingPlan.TIER_COUNTRIES.get(tier, [])
        for code in sorted(countries):
            name = PricingPlan.COUNTRY_NAMES.get(code, code)
            all_countries.append({
                'code': code,
                'name': name,
                'tier': tier
            })

    # Sort alphabetically by name
    return sorted(all_countries, key=lambda x: x['name'])

