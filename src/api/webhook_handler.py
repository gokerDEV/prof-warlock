"""
Webhook handler for processing incoming emails.

Orchestrates the complete email-to-AI-to-email workflow.
"""

import logging
from typing import Dict, Any
import json
import time
import os

from ..core.domain_models import IncomingEmail
from ..services.natal_chart_service import NatalChartService
from ..services.email_parser import EmailParsingService
from ..services.validation_service import ValidationService
from ..services.email_service import EmailService
from ..core.configuration import config


logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles the complete email processing workflow."""
    
    def __init__(self):
        self.email_parser = EmailParsingService()
        self.validator = ValidationService()
        self.natal_chart_service = NatalChartService()
        self.email_service = EmailService()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming webhook with complete email workflow.
        
        Args:
            webhook_data: Raw webhook data from email provider
            
        Returns:
            Dict: Processing result with status and details
        """
        # Save inbound email for debugging/testing (configurable)
        if config.save_inbound_emails:
            try:
                os.makedirs("inbound_emails", exist_ok=True)
                sender = webhook_data.get('From', 'unknown').replace('@', '_').replace('.', '_')
                timestamp = int(time.time())
                filename = f"inbound_emails/{timestamp}_{sender}.json"
                with open(filename, "w") as f:
                    json.dump(webhook_data, f, indent=2)
                logger.info(f"Saved inbound email: {filename}")
            except Exception as e:
                logger.error(f"Failed to save inbound email: {e}")
        
        try:
            # Parse incoming email
            email = self.email_parser.parse_webhook_data(webhook_data)
            logger.info(f"📧 Processing email from {email.from_name} ({email.from_email})")
            
            # Handle PING requests
            if email.is_ping_request:
                return await self._handle_ping_request(email)
            
            # Validate email for processing
            validation_error = self.validator.validate_email_for_processing(email)
            if validation_error:
                return await self._handle_validation_error(email, validation_error)
            
            # Process the submission
            return await self._process_submission(email)
            
        except Exception as e:
            logger.error(f"💥 Webhook processing error: {str(e)}")
            return {
                "status": "error",
                "message": f"Processing failed: {str(e)}"
            }
    
    async def _handle_ping_request(self, email: IncomingEmail) -> Dict[str, Any]:
        """Handle a PING request by sending a PONG response."""
        try:
            self.email_service.send_ping_response(email)
            return {
                "status": "success",
                "action": "pong_sent",
                "message": "PONG response sent"
            }
        except Exception as e:
            logger.error(f"Failed to send PONG response: {e}")
            return {
                "status": "error",
                "action": "pong_failed",
                "message": str(e)
            }
    
    async def _handle_validation_error(self, email: IncomingEmail, error) -> Dict[str, Any]:
        """Handle validation errors by sending appropriate error responses."""
        logger.info(f"❌ Validation error for {email.from_email}: {error.error_type}")
        
        success = self.email_service.send_error_response(email, error)
        
        return {
            "status": "success" if success else "error",
            "action": f"{error.error_type}_response_sent",
            "message": f"Error response sent: {error.error_type}" if success else "Failed to send error response"
        }
    
    async def _process_submission(self, email: IncomingEmail) -> Dict[str, Any]:
        """Process a valid submission for natal chart generation."""
        try:
            # Extract user info from email body
            user_info = self.natal_chart_service.parse_user_info(email.body)
            # Generate natal chart
            chart_bytes = self.natal_chart_service.generate_chart(user_info)
            # Send chart as attachment
            subject = "[Prof. Warlock] Your Natal Chart"
            content = f"Dear {user_info['First Name']}, your natal chart is ready! (Poster attached)"
            from src.core.domain_models import EmailAttachment
            attachment = EmailAttachment(
                name="natal_chart.png",
                content_type="image/png",
                content_length=len(chart_bytes),
                content=chart_bytes
            )
            from src.core.domain_models import EmailResponse
            response = EmailResponse(
                to_email=email.from_email,
                subject=subject,
                content=content,
                reply_to_message_id=email.message_id,
                attachments=[attachment]
            )
            success = self.email_service.send_response(response)
            if success:
                return {
                    "status": "success",
                    "action": "natal_chart_sent",
                    "file_processed": "natal_chart.png"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send natal chart email"
                }
        except Exception as e:
            logger.error(f"💥 Submission processing error: {str(e)}")
            fallback_message = self._create_fallback_message(email, str(e))
            success = self.email_service.send_feedback_response(email, fallback_message)
            return {
                "status": "partial_success" if success else "error",
                "action": "fallback_sent" if success else "processing_failed",
                "message": f"Sent fallback response due to: {str(e)}" if success else f"Complete failure: {str(e)}"
            }
    
    def _create_fallback_message(self, email: IncomingEmail, error_msg: str) -> str:
        """Create a fallback message when processing fails."""
        first_name = email.from_name.split()[0] if email.from_name else "Student"
        
        return f"""Dear {first_name},

Thank you for your submission. I've received your file but encountered a technical issue while analyzing it. Please try resubmitting, or contact me if the problem persists.

Best regards,
Prof. Warlock

(Technical details: {error_msg[:100]}...)""" 