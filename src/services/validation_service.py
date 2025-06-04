"""
Validation service for email attachments and requests.

Handles all validation logic with clear error reporting.
"""

from typing import Optional, Tuple

from ..core.domain_models import EmailAttachment, IncomingEmail, ValidationError
from ..core.configuration import config


class ValidationService:
    """Service for validating incoming emails for Prof. Warlock."""
    
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

        # Required fields
        required_fields = ["First Name:", "Last Name:", "Date of Birth:", "Place of Birth:"]
        missing_fields = [field for field in required_fields if field not in email.body]
        if missing_fields:
            return ValidationError(
                error_type="missing_user_info",
                message=f"Missing required fields: {', '.join(missing_fields)}",
                context={"from_email": email.from_email, "missing_fields": missing_fields}
            )
        return None 