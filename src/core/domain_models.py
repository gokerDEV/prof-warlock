"""
Domain models for Prof. Postmark.

Clean representation of core business entities.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class EmailAttachment:
    """Represents an email attachment (kept for possible future use, but not used in Prof. Warlock)."""
    name: str
    content_type: str
    content_length: int
    content: bytes
    content_id: Optional[str] = None


@dataclass
class IncomingEmail:
    """Represents an incoming email message for Prof. Warlock."""
    from_email: str
    from_name: str
    subject: str
    body: str
    attachments: List[EmailAttachment]
    message_id: Optional[str] = None
    
    @property
    def has_attachments(self) -> bool:
        """Check if email has any attachments."""
        return len(self.attachments) > 0
    
    @property
    def is_ping_request(self) -> bool:
        """Check if this is a PING health check request."""
        return "ping" in self.subject.lower() or "ping" in self.body.lower()


@dataclass
class EmailResponse:
    """Represents an outgoing email response."""
    
    to_email: str
    subject: str
    content: str
    reply_to_message_id: Optional[str] = None
    attachments: List[EmailAttachment] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class ProcessedImage:
    """Represents an image processed by the service."""

    image_path: str
    width: int
    height: int
    original_filename: str
    content_type: str
    scaled_content: bytes


class ValidationError:
    """Represents a validation error with context."""
    
    def __init__(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}" 