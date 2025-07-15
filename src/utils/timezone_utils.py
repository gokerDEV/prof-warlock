"""
Timezone utility for Prof. Warlock.

Provides common timezone conversion and parsing functions.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TimezoneUtils:
    """Utility class for timezone operations."""
    
    @staticmethod
    def convert_local_to_utc(local_datetime: datetime, timezone_offset: str) -> datetime:
        """
        Convert local datetime to UTC based on timezone offset.
        
        Args:
            local_datetime: Local datetime object
            timezone_offset: Timezone offset in format "+/-HH:MM" (e.g., "+03:00", "-05:00")
            
        Returns:
            datetime: UTC datetime
            
        Raises:
            ValueError: If timezone_offset is not in the correct format
        """
        if not timezone_offset:
            return local_datetime
        
        # Validate timezone format - must be +/-HH:MM
        if not re.match(r'^[+-]\d{1,2}:\d{2}$', timezone_offset):
            raise ValueError(f"Invalid timezone format: '{timezone_offset}'. Must be in +/-HH:MM format (e.g., +03:00, -05:00)")
            
        # Parse timezone offset
        sign = 1 if timezone_offset[0] == '+' else -1
        try:
            hours, minutes = map(int, timezone_offset[1:].split(':'))
        except ValueError:
            raise ValueError(f"Invalid timezone format: '{timezone_offset}'. Must be in +/-HH:MM format (e.g., +03:00, -05:00)")
        
        # Calculate offset in total minutes
        total_minutes = sign * (hours * 60 + minutes)
        
        # Convert to UTC by subtracting the timezone offset
        utc_datetime = local_datetime - timedelta(minutes=total_minutes)
        
        return utc_datetime
    
    @staticmethod
    def parse_timezone_offset(timezone_str: str) -> timedelta:
        """
        Parse timezone offset string and return timedelta object.
        
        Args:
            timezone_str: Timezone offset string like "+03:00" or "-05:00"
            
        Returns:
            timedelta: Timezone offset as timedelta object
            
        Raises:
            ValueError: If timezone format is invalid
        """
        if not timezone_str:
            return timedelta(0)
            
        # Parse timezone offset
        if timezone_str.startswith('+'):
            sign = 1
            offset_str = timezone_str[1:]
        elif timezone_str.startswith('-'):
            sign = -1
            offset_str = timezone_str[1:]
        else:
            sign = 1
            offset_str = timezone_str
        
        try:
            # Parse hours and minutes
            hours, minutes = map(int, offset_str.split(':'))
            offset = timedelta(hours=hours, minutes=minutes) * sign
            return offset
        except ValueError:
            raise ValueError(f"Invalid timezone format: '{timezone_str}'. Must be in +/-HH:MM format")
    
    @staticmethod
    def apply_timezone_offset(dt: datetime, timezone_offset: str, reverse: bool = False) -> datetime:
        """
        Apply timezone offset to datetime.
        
        Args:
            dt: Datetime object
            timezone_offset: Timezone offset string
            reverse: If True, subtract the offset instead of adding it
            
        Returns:
            datetime: Datetime with timezone offset applied
        """
        if not timezone_offset:
            return dt
            
        offset = TimezoneUtils.parse_timezone_offset(timezone_offset)
        
        if reverse:
            return dt - offset
        else:
            return dt + offset
    
    @staticmethod
    def validate_timezone_format(timezone_str: str) -> bool:
        """
        Validate timezone format.
        
        Args:
            timezone_str: Timezone string to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not timezone_str:
            return False
            
        return bool(re.match(r'^[+-]\d{1,2}:\d{2}$', timezone_str))
    
    @staticmethod
    def normalize_timezone_string(timezone_str: str) -> str:
        """
        Normalize timezone string to +/-HH:MM format.
        
        Args:
            timezone_str: Timezone string to normalize
            
        Returns:
            str: Normalized timezone string
            
        Raises:
            ValueError: If timezone format is invalid
        """
        if not timezone_str:
            return "+00:00"
            
        # If already in correct format, return as is
        if TimezoneUtils.validate_timezone_format(timezone_str):
            return timezone_str
        
        # Try to parse various formats
        # Handle formats like "+3", "-5", "3:00", etc.
        match = re.match(r'^([+-]?)(\d{1,2})(?::(\d{2}))?$', timezone_str.strip())
        if match:
            sign = match.group(1) or '+'
            hours = int(match.group(2))
            minutes = int(match.group(3)) if match.group(3) else 0
            
            return f"{sign}{hours:02d}:{minutes:02d}"
        
        raise ValueError(f"Cannot normalize timezone format: '{timezone_str}'. Expected +/-HH:MM format") 