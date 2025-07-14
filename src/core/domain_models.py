"""
Domain models for Prof. Warlock.

Clean representation of core business entities.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import re


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
    timezone: Optional[str] = Field(None, pattern=r'^[+-]\d{1,2}:\d{2}$')  # Format: +/-HH:MM
    lang: Optional[str] = "en"  # Language code: en, tr

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
                "longitude": -74.0060,
                "timezone": "+05:00",
                "lang": "en"
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
    timezone: Optional[str] = Field(None, pattern=r'^[+-]\d{1,2}:\d{2}$')  # Format: +/-HH:MM
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
                "timezone": "+05:00",
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        }


class NatalTransitRequest(BaseModel):
    """Request model for natal transit (classic) endpoint."""
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
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
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        }


class NatalTransitLocationRequest(BaseModel):
    """Request model for natal transit location (premium) endpoint."""
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
    current_location: str
    current_latitude: float
    current_longitude: float
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
                "current_location": "Los Angeles",
                "current_latitude": 34.0522,
                "current_longitude": -118.2437,
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        }


class NatalTransitRelocationRequest(BaseModel):
    """Request model for natal transit relocation (premium) endpoint."""
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
    relocation_location: str
    relocation_latitude: float
    relocation_longitude: float
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
                "relocation_location": "London",
                "relocation_latitude": 51.5074,
                "relocation_longitude": -0.1278,
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        }


class NatalDailyImageRequest(BaseModel):
    """Request model for natal daily image generation."""
    birth_day: int
    birth_month: int
    birth_year: int
    birth_time: str  # Format: HH:MM
    chart_type: str  # "classic", "location", "relocation"
    current_location: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    relocation_location: Optional[str] = None
    relocation_latitude: Optional[float] = None
    relocation_longitude: Optional[float] = None
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
                "chart_type": "classic",
                "today_day": 4,
                "today_month": 1,
                "today_year": 2024,
                "today_time": "15:30"
            }
        } 