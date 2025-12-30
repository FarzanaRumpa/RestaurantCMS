"""
Public Module Validation
Input validation and data sanitization for public module
"""
import re
from typing import Tuple, Dict, Any, List

class PublicValidator:
    """Validator for public module operations"""

    # Validation rules
    MAX_SEARCH_LENGTH = 100
    MIN_SEARCH_LENGTH = 2
    MAX_COMMENT_LENGTH = 1000
    MIN_RATING = 1
    MAX_RATING = 5

    @staticmethod
    def validate_search_request(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate search request

        Args:
            data (dict): Search request data

        Returns:
            tuple: (is_valid, errors)
        """
        errors = []

        # Check query exists
        if 'query' not in data:
            errors.append("Search query is required")
            return False, errors

        query = data.get('query', '').strip()

        # Validate query length
        if len(query) < PublicValidator.MIN_SEARCH_LENGTH:
            errors.append(f"Search query must be at least {PublicValidator.MIN_SEARCH_LENGTH} characters")

        if len(query) > PublicValidator.MAX_SEARCH_LENGTH:
            errors.append(f"Search query must not exceed {PublicValidator.MAX_SEARCH_LENGTH} characters")

        # Validate filters if provided
        if 'filters' in data:
            filters = data.get('filters')
            if not isinstance(filters, dict):
                errors.append("Filters must be a dictionary")

        return len(errors) == 0, errors

    @staticmethod
    def validate_feedback(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate feedback submission

        Args:
            data (dict): Feedback data

        Returns:
            tuple: (is_valid, errors)
        """
        errors = []

        # Validate rating
        if 'rating' in data:
            rating = data.get('rating')
            if not isinstance(rating, int):
                errors.append("Rating must be an integer")
            elif rating < PublicValidator.MIN_RATING or rating > PublicValidator.MAX_RATING:
                errors.append(f"Rating must be between {PublicValidator.MIN_RATING} and {PublicValidator.MAX_RATING}")

        # Validate comment
        if 'comment' in data:
            comment = data.get('comment', '').strip()
            if len(comment) > PublicValidator.MAX_COMMENT_LENGTH:
                errors.append(f"Comment must not exceed {PublicValidator.MAX_COMMENT_LENGTH} characters")

            # Check for spam/malicious content
            if PublicValidator._contains_spam(comment):
                errors.append("Comment contains prohibited content")

        # Validate email if provided
        if 'customer_email' in data:
            email = data.get('customer_email', '').strip()
            if email and not PublicValidator._is_valid_email(email):
                errors.append("Invalid email format")

        # Validate name
        if 'customer_name' in data:
            name = data.get('customer_name', '').strip()
            if len(name) > 100:
                errors.append("Name must not exceed 100 characters")

        return len(errors) == 0, errors

    @staticmethod
    def validate_restaurant_id(restaurant_id: Any) -> Tuple[bool, str]:
        """
        Validate restaurant ID

        Args:
            restaurant_id: Restaurant ID to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not restaurant_id:
            return False, "Restaurant ID is required"

        try:
            rest_id = int(restaurant_id)
            if rest_id <= 0:
                return False, "Invalid restaurant ID"
            return True, ""
        except (ValueError, TypeError):
            return False, "Restaurant ID must be a valid integer"

    @staticmethod
    def validate_pagination(page: Any, per_page: Any) -> Tuple[bool, Dict[str, int], List[str]]:
        """
        Validate pagination parameters

        Args:
            page: Page number
            per_page: Items per page

        Returns:
            tuple: (is_valid, validated_values, errors)
        """
        errors = []
        validated = {'page': 1, 'per_page': 20}

        # Validate page
        try:
            page_num = int(page)
            if page_num < 1:
                errors.append("Page number must be greater than 0")
            else:
                validated['page'] = page_num
        except (ValueError, TypeError):
            errors.append("Page must be a valid integer")

        # Validate per_page
        try:
            per_page_num = int(per_page)
            if per_page_num < 1:
                errors.append("Per page must be greater than 0")
            elif per_page_num > 100:
                errors.append("Per page cannot exceed 100")
            else:
                validated['per_page'] = per_page_num
        except (ValueError, TypeError):
            errors.append("Per page must be a valid integer")

        return len(errors) == 0, validated, errors

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input

        Args:
            text (str): Input text

        Returns:
            str: Sanitized text
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)

        # Trim whitespace
        text = text.strip()

        return text

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Check if email format is valid

        Args:
            email (str): Email address

        Returns:
            bool: True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def _contains_spam(text: str) -> bool:
        """
        Check if text contains spam patterns

        Args:
            text (str): Text to check

        Returns:
            bool: True if spam detected
        """
        spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'\b(?:viagra|cialis|pharmacy|casino|poker)\b',
            r'(?:\$\d+|\d+\$)',  # Money amounts
        ]

        text_lower = text.lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    @staticmethod
    def validate_table_number(table_number: Any) -> Tuple[bool, str]:
        """
        Validate table number

        Args:
            table_number: Table number to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not table_number:
            return False, "Table number is required"

        try:
            table_num = int(table_number)
            if table_num <= 0:
                return False, "Invalid table number"
            if table_num > 999:
                return False, "Table number too large"
            return True, ""
        except (ValueError, TypeError):
            return False, "Table number must be a valid integer"

