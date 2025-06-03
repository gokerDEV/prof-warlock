"""
Email sending service for outbound responses.

Handles email composition and delivery via Postmark.
"""

import requests
from typing import Dict, Optional
import mistune
import logging

from ..core.domain_models import EmailResponse, ValidationError, IncomingEmail
from ..core.configuration import config


class EmailService:
    """Service for sending email responses via Postmark."""
    
    def __init__(self):
        self.api_key = config.email.POSTMARK_API_KEY
        self.from_email = config.email.FROM_EMAIL
        self.base_url = "https://api.postmarkapp.com"
    
    def send_response(self, response: EmailResponse) -> bool:
        """
        Send an email response.
        
        Args:
            response: The email response to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            payload = self._build_email_payload(response)
            
            response_data = requests.post(
                f"{self.base_url}/email",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": self.api_key
                },
                json=payload,
                timeout=10
            )
            
            if response_data.status_code == 200:
                logging.info(f"Email sent successfully to {response.to_email}")
                return True
            else:
                logging.error(f"Failed to send email: {response_data.status_code} - {response_data.text}")
                return False
                
        except Exception as e:
            logging.error(f"Email sending error: {str(e)}", exc_info=True)
            return False
    
    def send_ping_response(self, email: IncomingEmail) -> bool:
        """Send a PONG response to a PING request."""
        response = EmailResponse(
            to_email=email.from_email,
            subject="Re: " + email.subject if email.subject else "PONG",
            content="PONG",
            reply_to_message_id=email.message_id
        )
        return self.send_response(response)
    
    def send_error_response(self, email: IncomingEmail, error: ValidationError) -> bool:
        """Send an error response for validation failures."""
        error_content = self._create_error_message(email.from_name, error)
        subject = self._create_error_subject(error.error_type)
        
        response = EmailResponse(
            to_email=email.from_email,
            subject=subject,
            content=error_content,
            reply_to_message_id=email.message_id
        )
        return self.send_response(response)
    
    def send_feedback_response(self, email: IncomingEmail, feedback_text: str, annotated_image: Optional[bytes] = None) -> bool:
        """Send AI-generated feedback response with optional annotated image."""
        # Convert markdown to HTML using mistune (with table support)
        html_content = self._markdown_to_html(feedback_text)
        
        response = EmailResponse(
            to_email=email.from_email,
            subject="[Prof. Postmark] Feedback for your submission",
            content=html_content,
            reply_to_message_id=email.message_id
        )
        
        # Add annotated image as attachment if available
        if annotated_image:
            import base64
            from ..core.domain_models import EmailAttachment
            
            attachment = EmailAttachment(
                name="annotated_feedback.jpg",
                content_type="image/jpeg",
                content_length=len(annotated_image),
                content=annotated_image
            )
            response.attachments = [attachment]
        
        return self.send_response(response)
    
    def _build_email_payload(self, response: EmailResponse) -> Dict:
        """Build the Postmark API payload."""
        payload = {
            "From": self.from_email,
            "To": response.to_email,
            "Subject": response.subject,
            "HtmlBody": response.content,
            "TextBody": self._html_to_text(response.content)
        }
        
        # DEBUG: Log the payload content
        logging.debug(f"Email payload debug: To: {payload['To']}, Subject: {payload['Subject']}, HtmlBody length: {len(payload['HtmlBody'])}, HtmlBody preview: {payload['HtmlBody'][:200]}..., TextBody length: {len(payload['TextBody'])}, Has <table>: {'<table>' in payload['HtmlBody']}")
        
        if response.reply_to_message_id:
            payload["InReplyTo"] = response.reply_to_message_id
        
        if response.attachments:
            import base64
            attachments = []
            for attachment in response.attachments:
                attachments.append({
                    "Name": attachment.name,
                    "Content": base64.b64encode(attachment.content).decode('utf-8'),
                    "ContentType": attachment.content_type
                })
            payload["Attachments"] = attachments
            logging.debug(f"Added {len(attachments)} attachments")
        
        return payload
    
    def _create_error_message(self, from_name: str, error: ValidationError) -> str:
        """Create a personalized error message."""
        first_name = self._extract_first_name(from_name)
        
        error_messages = {
            "no_attachment": f"""Dear {first_name},

Thank you for your email. I notice you didn't include any attachments. Please attach your work and resend your message.

Looking forward to reviewing your submission!

Best regards,
Prof. Postmark""",

            "file_too_large": f"""Dear {first_name},

Thank you for your submission. Your file exceeds our {config.file_validation.MAX_SIZE_MB}MB size limit. Please compress your file and resend.

If you need help reducing file size, try:
• Reducing image quality/resolution
• Converting to JPEG format
• Using online compression tools

Best regards,
Prof. Postmark""",

            "invalid_file_type": f"""Dear {first_name},

Thank you for your submission. Please submit files in one of these formats:
• JPEG (.jpg, .jpeg)
• PNG (.png)

Please convert your file and resend.

Best regards,
Prof. Postmark"""
        }
        
        return error_messages.get(error.error_type, f"""Dear {first_name},

Thank you for your submission. There was an issue processing your file: {error.message}

Please check your file and try again.

Best regards,
Prof. Postmark""")
    
    def _create_error_subject(self, error_type: str) -> str:
        """Create appropriate subject line for error type."""
        subjects = {
            "no_attachment": "[Prof. Postmark] Missing Attachment",
            "file_too_large": "[Prof. Postmark] File Too Large", 
            "invalid_file_type": "[Prof. Postmark] Invalid File Type"
        }
        return subjects.get(error_type, "[Prof. Postmark] Submission Error")
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML for email display using mistune with table support."""
        try:
            # Mistune 3.x: Table support is built-in
            markdown = mistune.create_markdown(plugins=["table"])
            html_content = markdown(markdown_text)
            return html_content
        except Exception as e:
            logging.error(f"Markdown conversion error: {e}", exc_info=True)
            return f"<pre>{markdown_text}</pre>"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML back to plain text for email fallback."""
        import re
        
        text = html_content
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up multiple line breaks
        text = re.sub(r'<br><br>', '\n\n', text)
        text = re.sub(r'<br>', '\n', text)
        
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
    
    def _extract_first_name(self, from_name: str) -> str:
        """Extract first name from full name or email."""
        if not from_name:
            return "Student"
        
        # Handle email addresses
        if "@" in from_name:
            from_name = from_name.split("@")[0]
        
        # Get first word/name
        first_part = from_name.split()[0] if from_name.split() else from_name
        
        # Clean up common email prefixes
        cleaned = first_part.replace(".", " ").replace("_", " ").replace("-", " ")
        return cleaned.split()[0].capitalize() if cleaned.split() else "Student" 