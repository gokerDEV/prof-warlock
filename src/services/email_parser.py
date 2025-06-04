"""
Email parsing service.

Handles parsing and cleaning of incoming email data from webhooks.
"""

import base64
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import logging

from ..core.domain_models import IncomingEmail, EmailAttachment


class EmailParsingService:
    """Service for parsing incoming email data from webhooks."""
    
    @staticmethod
    def parse_webhook_data(webhook_data: Dict[str, Any]) -> IncomingEmail:
        """
        Parse webhook data into a structured IncomingEmail object.
        
        Args:
            webhook_data: Raw webhook data from email provider
            
        Returns:
            IncomingEmail: Parsed email data
        """
        # Extract basic email fields
        from_email = webhook_data.get('From', '')
        from_name = webhook_data.get('FromName', from_email.split('@')[0])
        subject = webhook_data.get('Subject', '')
        message_id = webhook_data.get('MessageID')
        
        # Parse email body
        body = EmailParsingService._extract_clean_body(webhook_data)
        
        # Parse attachments
        attachments = EmailParsingService._parse_attachments(webhook_data)
        
        return IncomingEmail(
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body=body,
            attachments=attachments,
            message_id=message_id
        )
    
    @staticmethod
    def _extract_clean_body(webhook_data: Dict[str, Any]) -> str:
        """Extract and clean email body text."""
        # Try text first (preserves line breaks), then fallback to HTML
        text_body = webhook_data.get('TextBody', '')
        html_body = webhook_data.get('HtmlBody', '')
        
        if text_body:
            return text_body.strip()
        
        if html_body:
            return EmailParsingService._clean_html_content(html_body)
        
        return ""
    
    @staticmethod
    def _clean_html_content(html_content: str) -> str:
        """Clean HTML content and extract readable text while preserving line structure."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and preserve line breaks
            text = soup.get_text()
            # Clean up excessive whitespace but preserve line breaks
            lines = []
            for line in text.splitlines():
                cleaned_line = ' '.join(line.split())  # Clean internal whitespace
                if cleaned_line:  # Only keep non-empty lines
                    lines.append(cleaned_line)
            
            return '\n'.join(lines)
            
        except Exception:
            # Fallback: return HTML as-is if parsing fails
            return html_content
    
    @staticmethod
    def _parse_attachments(webhook_data: Dict[str, Any]) -> List[EmailAttachment]:
        """Parse email attachments from webhook data."""
        attachments = []
        attachment_data = webhook_data.get('Attachments', [])
        
        for attachment in attachment_data:
            try:
                # Decode base64 content
                content_b64 = attachment.get('Content', '')
                content_bytes = base64.b64decode(content_b64)
                
                email_attachment = EmailAttachment(
                    name=attachment.get('Name', 'unknown'),
                    content_type=attachment.get('ContentType', 'application/octet-stream'),
                    content_length=attachment.get('ContentLength', len(content_bytes)),
                    content=content_bytes,
                    content_id=attachment.get('ContentID')
                )
                
                attachments.append(email_attachment)
                
            except Exception as e:
                # Log error but continue processing other attachments
                logging.warning(f"Failed to parse attachment: {e}", exc_info=True)
                continue
        
        return attachments 