"""
Domain models for Prof. Warlock.

Clean representation of core business entities.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


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


class NatalChartRequest(BaseModel):
    """Request model for natal chart generation."""
    first_name: str
    last_name: str
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "birth_day": 1,
                "birth_month": 1,
                "birth_year": 1990,
                "birth_time": "12:00",
                "birth_place": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }


class NatalStatsRequest(BaseModel):
    """Request model for natal stats."""
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    today_day: Optional[int] = None
    today_month: Optional[int] = None
    today_year: Optional[int] = None
    today_time: Optional[str] = None  # Format: HH:MM

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "birth_day": 1,
                "birth_month": 1,
                "birth_year": 1990,
                "birth_time": "12:00",
                "birth_place": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        } 