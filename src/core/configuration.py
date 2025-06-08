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

class EmailConfig:
    """Email service settings."""
    POSTMARK_API_KEY = os.getenv("POSTMARK_API_KEY")
    DOMAIN = os.getenv("DOMAIN", "yourdomain.com")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "prof@yourdomain.com")

class SecurityConfig:
    """Security settings."""
    WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
    API_KEY = os.getenv("API_KEY")

class S3Config:
    """AWS S3 settings."""
    BUCKET = os.getenv("AWS_S3_BUCKET")
    PUBLIC_URL = os.getenv("AWS_S3_PUBLIC_URL")
    REGION = os.getenv("AWS_S3_REGION")
    ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

class AppConfig:
    """Main application configuration."""
    def __init__(self):
        self.file_validation = FileValidationConfig()
        self.email = EmailConfig()
        self.security = SecurityConfig()
        self.s3 = S3Config()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.save_inbound_emails = os.getenv("SAVE_INBOUND_EMAILS", "true").lower() == "true"
        self._validate_required_settings()

    def _validate_required_settings(self) -> None:
        """Check that all required environment variables are set."""
        required_env_vars = [
            ("POSTMARK_API_KEY", self.email.POSTMARK_API_KEY),
            ("WEBHOOK_SECRET_TOKEN", self.security.WEBHOOK_SECRET_TOKEN),
            ("API_KEY", self.security.API_KEY),
            ("AWS_S3_BUCKET", self.s3.BUCKET),
            ("AWS_S3_PUBLIC_URL", self.s3.PUBLIC_URL),
            ("AWS_S3_REGION", self.s3.REGION),
            ("AWS_ACCESS_KEY_ID", self.s3.ACCESS_KEY_ID),
            ("AWS_SECRET_ACCESS_KEY", self.s3.SECRET_ACCESS_KEY),
        ]
        for var_name, var_value in required_env_vars:
            if not var_value:
                raise ValueError(f"{var_name} environment variable is required")

# Global config instance
config = AppConfig() 