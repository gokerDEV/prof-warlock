"""
Validation service for email attachments and requests.

Handles all validation logic with clear error reporting.
"""

from typing import Optional, Tuple

from ..core.domain_models import EmailAttachment, IncomingEmail, ValidationError
from ..core.configuration import config


class ValidationService:
    """Service for validating email attachments and requests."""
    
    @staticmethod
    def validate_attachment(attachment: EmailAttachment) -> Optional[ValidationError]:
        """
        Validate an email attachment.
        
        Args:
            attachment: The attachment to validate
            
        Returns:
            ValidationError if invalid, None if valid
        """
        # Check file size
        if attachment.content_length > config.file_validation.MAX_SIZE_BYTES:
            return ValidationError(
                error_type="file_too_large",
                message=f"File size {attachment.content_length} bytes exceeds limit of {config.file_validation.MAX_SIZE_MB}MB",
                context={"filename": attachment.name, "size": attachment.content_length}
            )
        
        # Check MIME type
        if attachment.content_type not in config.file_validation.ALLOWED_MIME_TYPES:
            return ValidationError(
                error_type="invalid_file_type",
                message=f"File type {attachment.content_type} is not allowed",
                context={"filename": attachment.name, "content_type": attachment.content_type}
            )
        
        return None
    
    @staticmethod
    def validate_email_for_processing(email: IncomingEmail) -> Optional[ValidationError]:
        """
        Validate that an email can be processed for feedback.
        
        Args:
            email: The email to validate
            
        Returns:
            ValidationError if invalid, None if valid
        """
        # Skip validation for PING requests
        if email.is_ping_request:
            return None
        
        # Check for attachments
        if not email.has_attachments:
            return ValidationError(
                error_type="no_attachment",
                message="No attachments found in email",
                context={"from_email": email.from_email}
            )
        
        # Validate first attachment (assuming single file submissions)
        first_attachment = email.attachments[0]
        return ValidationService.validate_attachment(first_attachment) 