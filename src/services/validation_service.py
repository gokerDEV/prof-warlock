"""
Validation service for email attachments and requests.

Handles all validation logic with clear error reporting.
"""

from typing import Optional, Tuple
import re
from datetime import datetime

from ..core.domain_models import EmailAttachment, IncomingEmail, ValidationError
from ..core.configuration import config


class ValidationService:
    """Service for validating incoming emails for Prof. Warlock."""
    
    REQUIRED_FIELDS = [
        "First Name:",
        "Last Name:",
        "Date of Birth:",
        "Place of Birth:"
    ]

    DATE_TIME_PATTERN = r'\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{1,2}:\d{2}'
    
    @staticmethod
    def validate_email_for_processing(email: IncomingEmail) -> Optional[ValidationError]:
        """
        Validate that an email contains all required user info fields for natal chart generation.
        Args:
            email: The email to validate
        Returns:
            ValidationError if invalid, None if valid
        """
        # Skip validation for PING requests
        if email.is_ping_request:
            return None

        # Check for required fields
        missing_fields = [field for field in ValidationService.REQUIRED_FIELDS if field not in email.body]
        if missing_fields:
            return ValidationError(
                error_type="missing_user_info",
                message=f"Missing required fields: {', '.join(missing_fields)}",
                context={"from_email": email.from_email, "missing_fields": missing_fields}
            )

        # Validate date and time format
        date_match = re.search(fr'Date of Birth:\s*({ValidationService.DATE_TIME_PATTERN})', email.body)
        if not date_match:
            return ValidationError(
                error_type="invalid_date_format",
                message="Date of Birth must be in DD-MM-YYYY HH:MM format",
                context={"from_email": email.from_email}
            )

        return None 