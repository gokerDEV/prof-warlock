"""
Webhook handler for processing incoming emails.

Orchestrates the complete email-to-AI-to-email workflow.
"""

import logging
from typing import Dict, Any

from ..core.domain_models import IncomingEmail
from ..services.email_parser import EmailParsingService
from ..services.validation_service import ValidationService
from ..services.image_processor import ImageProcessingService
from ..services.ai_analysis_service import AIAnalysisService
from ..services.email_service import EmailService


logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles the complete email processing workflow."""
    
    def __init__(self):
        self.email_parser = EmailParsingService()
        self.validator = ValidationService()
        self.image_processor = ImageProcessingService()
        self.ai_service = AIAnalysisService()
        self.email_service = EmailService()
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming webhook with complete email workflow.
        
        Args:
            webhook_data: Raw webhook data from email provider
            
        Returns:
            Dict: Processing result with status and details
        """
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
        """Handle PING health check requests."""
        logger.info(f"🏥 PING request from {email.from_email}")
        
        success = self.email_service.send_ping_response(email)
        
        return {
            "status": "success" if success else "error",
            "action": "pong_sent",
            "message": "PONG response sent" if success else "Failed to send PONG"
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
        """Process a valid submission with AI analysis."""
        try:
            # Get the first attachment (assuming single file submissions)
            attachment = email.attachments[0]
            logger.info(f"📎 Processing attachment: {attachment.name}")
            
            # Check if it's an image
            if attachment.content_type in ['image/jpeg', 'image/png', 'image/jpg']:
                # Process image
                processed_image = self.image_processor.process_image_attachment(attachment)
                logger.info(f"🖼️ Image processed: {processed_image.width}x{processed_image.height}")
                
                # Analyze with AI
                analysis_result = self.ai_service.analyze_submission(email, processed_image)
            else:
                # Text-only analysis
                analysis_result = self.ai_service.analyze_submission(email)
            
            logger.info(f"🧠 AI analysis completed: {analysis_result.analysis_type}")
            
            # Send feedback response with annotated image if available
            success = self.email_service.send_feedback_response(
                email, 
                analysis_result.feedback_text,
                analysis_result.annotated_image
            )
            
            if success:
                logger.info(f"📬 Feedback sent successfully to {email.from_email}")
                return {
                    "status": "success",
                    "action": "feedback_sent",
                    "analysis_type": analysis_result.analysis_type,
                    "file_processed": attachment.name,
                    "has_annotation": analysis_result.has_annotation
                }
            else:
                logger.error(f"❌ Failed to send feedback to {email.from_email}")
                return {
                    "status": "error",
                    "message": "Failed to send feedback email"
                }
                
        except Exception as e:
            logger.error(f"💥 Submission processing error: {str(e)}")
            
            # Send fallback response
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
Prof. Postmark

(Technical details: {error_msg[:100]}...)""" 