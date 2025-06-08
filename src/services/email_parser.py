"""
Email parsing service with BERT-powered understanding.

Handles parsing and cleaning of incoming email data using transformer models.
"""

import base64
import email
from email import policy
from email.parser import Parser
from typing import Dict, Any, List, Union
from bs4 import BeautifulSoup
import logging
import re
from transformers import pipeline
import torch
from dateutil import parser as date_parser

from ..core.domain_models import IncomingEmail, EmailAttachment


class EmailParsingService:
    """Service for parsing incoming email data using transformers."""
    
    _qa_pipeline = None
    
    def __init__(self):
        """Initialize transformer models for email understanding."""
        try:
            # Field extraction patterns
            self.field_patterns = {
                'name': r'First Name:\s*([^\n]+)',
                'last_name': r'Last Name:\s*([^\n]+)',
                'birth_date': r'Date of Birth:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4}(?:\s+\d{1,2}:\d{2})?)',
                'birth_place': r'Place of Birth:\s*([^\n]+)',
            }
            
            # Common signature markers
            self.signature_markers = [
                r'--\s*\n',  # Standard signature delimiter
                r'Best regards,',
                r'Sincerely,',
                r'Thanks,',
                r'Cheers,',
            ]
            
            logging.info("Email parser initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize email parser: {str(e)}")
            raise
    
    @staticmethod
    def _get_qa_pipeline():
        """Lazily load the HuggingFace QA pipeline."""
        if EmailParsingService._qa_pipeline is None:
            EmailParsingService._qa_pipeline = pipeline(
                "question-answering",
                model="distilbert-base-uncased-distilled-squad",
            )
        return EmailParsingService._qa_pipeline
    
    def _remove_signature(self, text: str) -> str:
        """Remove email signature from text."""
        # First try to split on standard signature delimiter
        parts = text.split('\n--\n')
        if len(parts) > 1:
            return parts[0].strip()
        
        # If no standard delimiter, try to find signature start
        lines = text.split('\n')
        signature_start = -1
        
        for i, line in enumerate(lines):
            # Check for signature markers
            for marker in self.signature_markers:
                if re.search(marker, line, re.IGNORECASE):
                    signature_start = i
                    break
            if signature_start != -1:
                break
        
        if signature_start != -1:
            return '\n'.join(lines[:signature_start]).strip()
        
        return text.strip()
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        # Remove signature first
        text = self._remove_signature(text)
        
        # Remove multiple newlines and spaces
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _parse_with_transformers(self, body: str) -> Dict[str, str]:
        """Extract information using transformer QA model."""
        qa = self._get_qa_pipeline()
        questions = {
            "name": "What is the first name?",
            "last_name": "What is the last name?",
            "birth_date": "What is the date of birth?",
            "birth_time": "What is the time of birth?",
            "birth_place": "Where was the person born?"
        }
        
        answers = {}
        for key, question in questions.items():
            try:
                result = qa(question=question, context=body)
                answer = result.get("answer", "").strip()
                if answer:
                    answers[key] = answer
            except Exception as e:
                logging.warning(f"Transformers parsing failed for {key}: {e}")
        
        # Parse date and time if both are present
        if 'birth_date' in answers and 'birth_time' in answers:
            try:
                # Parse date and time separately
                date_str = answers['birth_date']
                time_str = answers['birth_time']
                
                # Try to parse date
                parsed_date = date_parser.parse(date_str)
                date_formatted = parsed_date.strftime("%d-%m-%Y")
                
                # Try to parse time
                parsed_time = date_parser.parse(time_str)
                time_formatted = parsed_time.strftime("%H:%M")
                
                # Combine them
                answers['birth_date'] = f"{date_formatted} {time_formatted}"
                
            except Exception as e:
                logging.warning(f"Failed to parse date/time: {e}")
        
        return answers
    
    def extract_birth_info(self, text: str) -> Dict[str, str]:
        """
        Extract birth information using transformers QA model.
        Falls back to regex patterns if QA extraction fails.
        """
        try:
            # Clean and normalize text
            cleaned_text = self._preprocess_text(text)
            
            # Try transformers first
            info = self._parse_with_transformers(cleaned_text)
            
            # If transformers failed to find some fields, try regex
            if not all(key in info for key in ['name', 'last_name', 'birth_date', 'birth_place']):
                regex_info = self._extract_with_regex(cleaned_text)
                info.update({k: v for k, v in regex_info.items() if k not in info})
            
            return info
            
        except Exception as e:
            logging.error(f"Transformer extraction failed: {str(e)}, falling back to regex")
            return self._extract_with_regex(text)
    
    def _extract_with_regex(self, text: str) -> Dict[str, str]:
        """Extract information using regex patterns as fallback."""
        info = {}
        for field, pattern in self.field_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info[field] = match.group(1).strip()
        return info
    
    @staticmethod
    def parse_email(data: Union[Dict[str, Any], str]) -> IncomingEmail:
        """
        Parse email data into a structured IncomingEmail object.
        Handles both webhook data and raw email format.
        
        Args:
            data: Either raw webhook data from email provider or raw email string
            
        Returns:
            IncomingEmail: Parsed email data
        """
        parser_service = EmailParsingService()
        
        if isinstance(data, dict):
            return parser_service.parse_webhook_data(data)
        elif isinstance(data, str):
            return parser_service.parse_raw_email(data)
        else:
            raise ValueError("Input must be either webhook data dict or raw email string")

    def parse_raw_email(self, raw_email: str) -> IncomingEmail:
        """
        Parse raw email format into IncomingEmail object using transformers.
        
        Args:
            raw_email: Raw email string
            
        Returns:
            IncomingEmail: Parsed email data
        """
        try:
            # Parse raw email using email.parser
            parser = Parser(policy=policy.default)
            msg = parser.parsestr(raw_email)
            
            # Extract basic fields
            from_email = msg.get('From', '')
            if '<' in from_email and '>' in from_email:
                from_name = from_email.split('<')[0].strip()
                from_email = from_email.split('<')[1].split('>')[0].strip()
            else:
                from_name = from_email.split('@')[0]
            
            subject = msg.get('Subject', '')
            message_id = msg.get('Message-ID')
            
            # Get body with transformer understanding
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()
            
            # Extract birth information using transformers
            birth_info = self.extract_birth_info(body)
            
            # If birth info found, format body accordingly
            if birth_info:
                # Combine date and time if both are present
                date_str = birth_info.get('birth_date', '')
                time_str = birth_info.get('birth_time', '')
                if date_str and time_str and not ' ' in date_str:  # If date doesn't already have time
                    date_str = f"{date_str} {time_str}"
                
                body = f"""First Name: {birth_info.get('name', '')}
Last Name: {birth_info.get('last_name', '')}
Date of Birth: {date_str}
Place of Birth: {birth_info.get('birth_place', '')}"""
            
            # Parse attachments if any
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                        
                    filename = part.get_filename()
                    if filename:
                        content = part.get_payload(decode=True)
                        attachment = EmailAttachment(
                            name=filename,
                            content_type=part.get_content_type(),
                            content_length=len(content),
                            content=content,
                            content_id=part.get('Content-ID')
                        )
                        attachments.append(attachment)
            
            return IncomingEmail(
                from_email=from_email,
                from_name=from_name,
                subject=subject,
                body=body.strip(),
                attachments=attachments,
                message_id=message_id
            )
            
        except Exception as e:
            logging.error(f"Failed to parse raw email: {str(e)}", exc_info=True)
            raise
    
    def _format_date_time(self, date_str: str, time_str: str) -> str:
        """
        Format date and time strings into the required format (DD-MM-YYYY HH:MM).
        Handles various date formats including natural language.
        """
        try:
            # Parse the date
            parsed_date = date_parser.parse(date_str)
            
            # Parse the time if provided
            if time_str:
                parsed_time = date_parser.parse(time_str)
                # Combine date and time
                parsed_date = parsed_date.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute
                )
            
            # Format to required format
            return parsed_date.strftime("%d-%m-%Y %H:%M")
        except Exception as e:
            logging.warning(f"Failed to parse date/time: {e}")
            return f"{date_str} {time_str}".strip()

    def parse_webhook_data(self, webhook_data: Dict[str, Any]) -> IncomingEmail:
        """
        Parse webhook data into a structured IncomingEmail object using transformers.
        
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
        
        # Get original body
        body = self._extract_clean_body(webhook_data)
        
        # Try to extract birth information using transformers
        try:
            birth_info = self.extract_birth_info(body)
            if birth_info and all(birth_info.get(k) for k in ['name', 'last_name', 'birth_date', 'birth_place']):
                body = f"""First Name: {birth_info['name']}
Last Name: {birth_info['last_name']}
Date of Birth: {birth_info['birth_date']}
Place of Birth: {birth_info['birth_place']}"""
        except Exception as e:
            logging.warning(f"Failed to extract birth info: {e}")
            # Keep original body on failure
        
        # Parse attachments
        attachments = self._parse_attachments(webhook_data)
        
        return IncomingEmail(
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body=body.strip(),
            attachments=attachments,
            message_id=message_id
        )
    
    def _extract_clean_body(self, webhook_data: Dict[str, Any]) -> str:
        """Extract and clean email body from webhook data."""
        try:
            # Try text first (preserves line breaks)
            body = webhook_data.get('TextBody', '')
            if body:
                return self._preprocess_text(body)
            
            # Fallback to HTML
            body = webhook_data.get('HtmlBody', '')
            if body:
                return self._preprocess_text(self._clean_html_content(body))
            
            return ""
        except Exception as e:
            logging.error(f"Failed to extract body: {e}")
            return ""
    
    @staticmethod
    def _clean_html_content(html_content: str) -> str:
        """Clean HTML content and extract text."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text()
        except Exception as e:
            logging.error(f"Failed to clean HTML: {e}")
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