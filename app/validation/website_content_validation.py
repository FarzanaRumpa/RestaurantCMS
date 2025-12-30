"""
Website Content Validation
Input validation for website content models
"""
import re
from typing import Tuple, List, Dict, Any

class WebsiteContentValidator:
    """Validator for website content CRUD operations"""

    # ========================================================================
    # HERO SECTION VALIDATION
    # ========================================================================

    @staticmethod
    def validate_hero_section(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate hero section data"""
        errors = []

        # Title is required for creation
        if not is_update and not data.get('title'):
            errors.append('Title is required')

        # Title length
        if data.get('title') and len(data['title']) > 200:
            errors.append('Title must not exceed 200 characters')

        # CTA text length
        if data.get('cta_text') and len(data['cta_text']) > 100:
            errors.append('CTA text must not exceed 100 characters')

        # URL validation
        if data.get('cta_link') and not WebsiteContentValidator._is_valid_url(data['cta_link']):
            errors.append('CTA link must be a valid URL')

        # Display order
        if 'display_order' in data:
            if not isinstance(data['display_order'], int) or data['display_order'] < 0:
                errors.append('Display order must be a non-negative integer')

        return len(errors) == 0, errors

    # ========================================================================
    # FEATURE VALIDATION
    # ========================================================================

    @staticmethod
    def validate_feature(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate feature data"""
        errors = []

        # Required fields for creation
        if not is_update:
            if not data.get('title'):
                errors.append('Title is required')
            if not data.get('description'):
                errors.append('Description is required')

        # Title length
        if data.get('title') and len(data['title']) > 200:
            errors.append('Title must not exceed 200 characters')

        # Icon or icon_image should be provided
        if not is_update and not data.get('icon') and not data.get('icon_image'):
            errors.append('Either icon or icon_image must be provided')

        # URL validation for link
        if data.get('link') and not WebsiteContentValidator._is_valid_url(data['link']):
            errors.append('Link must be a valid URL')

        return len(errors) == 0, errors

    # ========================================================================
    # HOW IT WORKS STEP VALIDATION
    # ========================================================================

    @staticmethod
    def validate_how_it_works_step(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate how it works step data"""
        errors = []

        # Required fields
        if not is_update:
            if not data.get('step_number'):
                errors.append('Step number is required')
            if not data.get('title'):
                errors.append('Title is required')
            if not data.get('description'):
                errors.append('Description is required')

        # Step number validation
        if 'step_number' in data:
            if not isinstance(data['step_number'], int) or data['step_number'] < 1:
                errors.append('Step number must be a positive integer')

        # Title length
        if data.get('title') and len(data['title']) > 200:
            errors.append('Title must not exceed 200 characters')

        return len(errors) == 0, errors

    # ========================================================================
    # PRICING PLAN VALIDATION
    # ========================================================================

    @staticmethod
    def validate_pricing_plan(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate pricing plan data"""
        errors = []

        # Required fields for creation
        if not is_update:
            if not data.get('name'):
                errors.append('Name is required')
            if 'price' not in data:
                errors.append('Price is required')
            if not data.get('features'):
                errors.append('Features are required')

        # Name length
        if data.get('name') and len(data['name']) > 100:
            errors.append('Name must not exceed 100 characters')

        # Price validation
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    errors.append('Price must be non-negative')
            except (ValueError, TypeError):
                errors.append('Price must be a valid number')

        # Currency validation
        if data.get('currency'):
            if not re.match(r'^[A-Z]{3}$', data['currency']):
                errors.append('Currency must be a 3-letter ISO code (e.g., USD, EUR)')

        # Price period validation
        if data.get('price_period'):
            valid_periods = ['month', 'year', 'one-time', 'week', 'day']
            if data['price_period'] not in valid_periods:
                errors.append(f'Price period must be one of: {", ".join(valid_periods)}')

        # Limits validation
        for field in ['max_restaurants', 'max_menu_items', 'max_orders_per_month']:
            if field in data and data[field] is not None:
                if not isinstance(data[field], int) or data[field] < 0:
                    errors.append(f'{field} must be a non-negative integer')

        return len(errors) == 0, errors

    # ========================================================================
    # TESTIMONIAL VALIDATION
    # ========================================================================

    @staticmethod
    def validate_testimonial(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate testimonial data"""
        errors = []

        # Required fields
        if not is_update:
            if not data.get('customer_name'):
                errors.append('Customer name is required')
            if not data.get('message'):
                errors.append('Message is required')

        # Name length
        if data.get('customer_name') and len(data['customer_name']) > 100:
            errors.append('Customer name must not exceed 100 characters')

        # Message length
        if data.get('message'):
            if len(data['message']) < 20:
                errors.append('Message must be at least 20 characters')
            if len(data['message']) > 1000:
                errors.append('Message must not exceed 1000 characters')

        # Rating validation
        if 'rating' in data and data['rating'] is not None:
            if not isinstance(data['rating'], int) or data['rating'] < 1 or data['rating'] > 5:
                errors.append('Rating must be between 1 and 5')

        # Avatar URL validation
        if data.get('avatar_url') and not WebsiteContentValidator._is_valid_url(data['avatar_url']):
            errors.append('Avatar URL must be a valid URL')

        return len(errors) == 0, errors

    # ========================================================================
    # FAQ VALIDATION
    # ========================================================================

    @staticmethod
    def validate_faq(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate FAQ data"""
        errors = []

        # Required fields
        if not is_update:
            if not data.get('question'):
                errors.append('Question is required')
            if not data.get('answer'):
                errors.append('Answer is required')

        # Question length
        if data.get('question'):
            if len(data['question']) < 10:
                errors.append('Question must be at least 10 characters')
            if len(data['question']) > 500:
                errors.append('Question must not exceed 500 characters')

        # Answer length
        if data.get('answer'):
            if len(data['answer']) < 20:
                errors.append('Answer must be at least 20 characters')

        # Category length
        if data.get('category') and len(data['category']) > 100:
            errors.append('Category must not exceed 100 characters')

        return len(errors) == 0, errors

    # ========================================================================
    # CONTACT INFO VALIDATION
    # ========================================================================

    @staticmethod
    def validate_contact_info(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate contact info data"""
        errors = []

        # At least one contact method required
        if not is_update:
            if not any([data.get('email'), data.get('phone'), data.get('address')]):
                errors.append('At least one contact method (email, phone, or address) is required')

        # Email validation
        if data.get('email') and not WebsiteContentValidator._is_valid_email(data['email']):
            errors.append('Invalid email format')

        # Phone validation
        if data.get('phone') and not WebsiteContentValidator._is_valid_phone(data['phone']):
            errors.append('Invalid phone format')

        # Website URL validation
        if data.get('website') and not WebsiteContentValidator._is_valid_url(data['website']):
            errors.append('Website must be a valid URL')

        # Field lengths
        length_limits = {
            'label': 100,
            'email': 120,
            'phone': 20,
            'city': 100,
            'state': 100,
            'country': 100,
            'postal_code': 20,
            'support_hours': 200
        }

        for field, limit in length_limits.items():
            if data.get(field) and len(data[field]) > limit:
                errors.append(f'{field} must not exceed {limit} characters')

        return len(errors) == 0, errors

    # ========================================================================
    # FOOTER LINK VALIDATION
    # ========================================================================

    @staticmethod
    def validate_footer_link(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate footer link data"""
        errors = []

        # Required fields
        if not is_update:
            if not data.get('title'):
                errors.append('Title is required')
            if not data.get('url'):
                errors.append('URL is required')

        # Title length
        if data.get('title') and len(data['title']) > 200:
            errors.append('Title must not exceed 200 characters')

        # URL validation
        if data.get('url') and not WebsiteContentValidator._is_valid_url(data['url']):
            errors.append('URL must be valid')

        # Section length
        if data.get('section') and len(data['section']) > 100:
            errors.append('Section must not exceed 100 characters')

        # Target validation
        if data.get('target'):
            valid_targets = ['_self', '_blank', '_parent', '_top']
            if data['target'] not in valid_targets:
                errors.append(f'Target must be one of: {", ".join(valid_targets)}')

        return len(errors) == 0, errors

    # ========================================================================
    # FOOTER CONTENT VALIDATION
    # ========================================================================

    @staticmethod
    def validate_footer_content(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate footer content data"""
        errors = []

        # URL validations for social media and app stores
        url_fields = [
            'logo_url', 'facebook_url', 'twitter_url', 'instagram_url',
            'linkedin_url', 'youtube_url', 'app_store_url', 'play_store_url'
        ]

        for field in url_fields:
            if data.get(field) and not WebsiteContentValidator._is_valid_url(data[field]):
                errors.append(f'{field} must be a valid URL')

        # Tagline length
        if data.get('tagline') and len(data['tagline']) > 500:
            errors.append('Tagline must not exceed 500 characters')

        # Newsletter text length
        if data.get('newsletter_text') and len(data['newsletter_text']) > 500:
            errors.append('Newsletter text must not exceed 500 characters')

        return len(errors) == 0, errors

    # ========================================================================
    # SOCIAL MEDIA LINK VALIDATION
    # ========================================================================

    @staticmethod
    def validate_social_media(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, List[str]]:
        """Validate social media link data"""
        errors = []

        # Required fields
        if not is_update:
            if not data.get('platform'):
                errors.append('Platform is required')
            if not data.get('url'):
                errors.append('URL is required')

        # Platform length
        if data.get('platform') and len(data['platform']) > 50:
            errors.append('Platform name must not exceed 50 characters')

        # URL validation
        if data.get('url') and not WebsiteContentValidator._is_valid_url(data['url']):
            errors.append('URL must be valid')

        # Icon validation
        if data.get('icon') and len(data['icon']) > 100:
            errors.append('Icon class must not exceed 100 characters')

        return len(errors) == 0, errors

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False

        # Allow relative URLs starting with /
        if url.startswith('/'):
            return True

        # Validate absolute URLs
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False

        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email))

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone format"""
        if not phone:
            return False

        # Allow various phone formats
        phone_pattern = re.compile(
            r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$'
        )
        return bool(phone_pattern.match(phone))

