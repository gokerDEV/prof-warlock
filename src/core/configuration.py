"""
Application configuration management.

Minimal configuration with only required settings for the new OpenAI Responses API.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FileValidationConfig:
    """File validation rules."""
    MAX_SIZE_MB = 5
    MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
    ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/jpg"]

class AIServiceConfig:
    """OpenAI API settings (Responses API, no assistant/thread IDs)."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EmailConfig:
    """Email service settings."""
    POSTMARK_API_KEY = os.getenv("POSTMARK_API_KEY")
    DOMAIN = os.getenv("DOMAIN", "yourdomain.com")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "prof@yourdomain.com")

class SecurityConfig:
    """Security settings."""
    WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

class AppConfig:
    """Main application configuration."""
    def __init__(self):
        self.file_validation = FileValidationConfig()
        self.ai_service = AIServiceConfig()
        self.email = EmailConfig()
        self.security = SecurityConfig()
        self._validate_required_settings()

    def _validate_required_settings(self) -> None:
        """Check that all required environment variables are set."""
        required_env_vars = [
            ("POSTMARK_API_KEY", self.email.POSTMARK_API_KEY),
            ("OPENAI_API_KEY", self.ai_service.OPENAI_API_KEY),
            ("WEBHOOK_SECRET_TOKEN", self.security.WEBHOOK_SECRET_TOKEN),
        ]
        for var_name, var_value in required_env_vars:
            if not var_value:
                raise ValueError(f"{var_name} environment variable is required")

# Global config instance
config = AppConfig() 