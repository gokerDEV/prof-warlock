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
            subject="[Prof. Warlock] Feedback for your submission",
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
            "From": f"Prof. Warlock <{self.from_email}>",  # Include sender name
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
        """Create a personalized error message with proper HTML formatting."""
        first_name = self._extract_first_name(from_name)
        
        error_messages = {
            "missing_user_info": f"""<p>Dear {first_name},</p>

<p>Some information is missing. Please reply using the format:</p>
<p>
First Name: ...<br>
Last Name: ...<br>
Date of Birth: DD-MM-YYYY HH:MM<br>
Place of Birth: ...
</p>

<p>Best regards,<br>
Prof. Warlock</p>""",

            "invalid_date_format": f"""<p>Dear {first_name},</p>

<p>The Date of Birth format is incorrect. Please use the format DD-MM-YYYY HH:MM (e.g., 01-01-1990 14:30).</p>

<p>Best regards,<br>
Prof. Warlock</p>""",

            "invalid_time_format": f"""<p>Dear {first_name},</p>

<p>The Time of Birth format is incorrect. Please use the format HH:MM in 24-hour format (e.g., 14:30 for 2:30 PM).</p>

<p>Best regards,<br>
Prof. Warlock</p>"""
        }
        
        return error_messages.get(error.error_type, f"""<p>Dear {first_name},</p>

<p>Thank you for your submission. There was an issue processing your request: {error.message}</p>

<p>Please check your submission and try again.</p>

<p>Best regards,<br>
Prof. Warlock</p>""")
    
    def _create_error_subject(self, error_type: str) -> str:
        """Create appropriate subject line for error type."""
        subjects = {
            "missing_user_info": "[Prof. Warlock] Missing Information",
            "invalid_date_format": "[Prof. Warlock] Invalid Date Format",
            "invalid_time_format": "[Prof. Warlock] Invalid Time Format"
        }
        return subjects.get(error_type, "[Prof. Warlock] Submission Error")
    
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