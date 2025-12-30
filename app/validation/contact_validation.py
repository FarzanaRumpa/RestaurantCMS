"""
Contact Form Validation
Input validation and spam protection
"""
import re
from typing import Tuple, List, Dict, Any


class ContactFormValidator:
    """Validator for contact form submissions"""

    # Spam keywords (common spam patterns)
    SPAM_KEYWORDS = [
        'viagra', 'cialis', 'casino', 'lottery', 'bitcoin', 'cryptocurrency',
        'click here', 'buy now', 'limited time', 'act now', 'free money',
        'work from home', 'make money fast', 'weight loss', 'diet pills'
    ]

    @staticmethod
    def validate_contact_form(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate contact form submission
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        if not data.get('name') or not data['name'].strip():
            errors.append('Name is required')
        elif len(data['name']) < 2:
            errors.append('Name must be at least 2 characters')
        elif len(data['name']) > 100:
            errors.append('Name must not exceed 100 characters')

        # Email validation
        if not data.get('email') or not data['email'].strip():
            errors.append('Email is required')
        elif not ContactFormValidator._is_valid_email(data['email']):
            errors.append('Invalid email format')
        elif len(data['email']) > 120:
            errors.append('Email must not exceed 120 characters')

        # Message validation
        if not data.get('message') or not data['message'].strip():
            errors.append('Message is required')
        elif len(data['message']) < 10:
            errors.append('Message must be at least 10 characters')
        elif len(data['message']) > 5000:
            errors.append('Message must not exceed 5000 characters')

        # Optional phone validation
        if data.get('phone') and data['phone'].strip():
            if not ContactFormValidator._is_valid_phone(data['phone']):
                errors.append('Invalid phone format')
            elif len(data['phone']) > 20:
                errors.append('Phone must not exceed 20 characters')

        # Optional subject validation
        if data.get('subject') and len(data['subject']) > 200:
            errors.append('Subject must not exceed 200 characters')

        return len(errors) == 0, errors

    @staticmethod
    def check_spam(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Basic spam detection
        Returns: (is_spam, reason)
        """
        message = data.get('message', '').lower()
        name = data.get('name', '').lower()
        subject = data.get('subject', '').lower()

        # Check for spam keywords
        for keyword in ContactFormValidator.SPAM_KEYWORDS:
            if keyword in message or keyword in subject:
                return True, f'Spam keyword detected: {keyword}'

        # Check for excessive URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, data.get('message', ''))
        if len(urls) > 3:
            return True, 'Too many URLs in message'

        # Check for excessive capitalization
        if message and len(message) > 20:
            caps_count = sum(1 for c in message if c.isupper())
            if caps_count / len(message) > 0.5:
                return True, 'Excessive capitalization'

        # Check for repeated characters
        if re.search(r'(.)\1{10,}', message):
            return True, 'Repeated characters detected'

        # Check for suspicious patterns (all numbers in name)
        if name and name.replace(' ', '').isdigit():
            return True, 'Suspicious name pattern'

        # Check for very short messages with URLs
        if len(message.split()) < 5 and len(urls) > 0:
            return True, 'Suspicious short message with links'

        return False, ''

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False

        # Basic email regex
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email.strip()))

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone format"""
        if not phone:
            return True  # Phone is optional

        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone.strip())

        # Check if remaining is mostly digits with optional + at start
        phone_pattern = re.compile(r'^\+?[\d]{7,15}$')
        return bool(phone_pattern.match(cleaned))

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Basic input sanitization"""
        if not text:
            return ''

        # Remove null bytes
        text = text.replace('\x00', '')

        # Strip excessive whitespace
        text = ' '.join(text.split())

        return text.strip()

