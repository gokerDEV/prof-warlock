"""
Comprehensive test suite for Prof. Warlock service.
Combines all tests for email parsing, chart generation, and system functionality.
"""

import os
import base64
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.services.email_parser import EmailParsingService
from src.services.validation_service import ValidationService
from src.services.natal_chart_service import NatalChartService
from src.services.email_service import EmailService
from src.core.domain_models import IncomingEmail, ValidationError, EmailResponse
from src.api.main import app
from src.core.configuration import config

# Test client setup
client = TestClient(app)

# Fixtures
@pytest.fixture(autouse=True)
def reset_qa_pipeline():
    """Reset the QA pipeline singleton before each test."""
    NatalChartService._qa_pipeline = None
    yield
    NatalChartService._qa_pipeline = None

# Email Parsing Tests
class TestEmailParsing:
    def test_parse_email_with_user_info(self):
        """Test parsing email with standard format user info."""
        body = (
            "First Name: Jane\n"
            "Last Name: Doe\n"
            "Date of Birth: 15-06-1985 12:10\n"
            "Place of Birth: San Francisco, California, USA\n"
        )
        webhook_data = {
            'From': 'jane.doe@example.com',
            'FromName': 'Jane Doe',
            'Subject': 'Natal Chart Request',
            'TextBody': body,
            'Attachments': []
        }

        # Mock transformer responses
        mock_responses = {
            "What is the first name?": {"answer": "Jane"},
            "What is the last name?": {"answer": "Doe"},
            "What is the date of birth?": {"answer": "15-06-1985"},
            "What is the time of birth?": {"answer": "12:10"},
            "Where was the person born?": {"answer": "San Francisco, California, USA"}
        }
        
        def mock_qa_side_effect(**kwargs):
            return mock_responses[kwargs["question"]]
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(EmailParsingService, '_get_qa_pipeline', return_value=mock_qa):
                parser = EmailParsingService()
                email = parser.parse_webhook_data(webhook_data)
                assert email.body.strip() == body.strip()
                for field in ["First Name:", "Last Name:", "Date of Birth:", "Place of Birth:"]:
                    assert field in email.body
                assert email.from_email == 'jane.doe@example.com'
                assert email.from_name == 'Jane Doe'
                assert email.attachments == []

    def test_inbound_email_parsing_with_mock_data(self):
        """Test email parsing with mock inbound email data."""
        mock_webhook_data = {
            'From': 'john.doe@example.com',
            'FromName': 'John Doe', 
            'Subject': 'natal chart',
            'TextBody': """---------- Forwarded message ---------
From: John Doe <john.doe@example.com>
Date: Wed, Jun 4, 2025 at 4:40 PM
Subject: natal chart
To: <warlock@example.com>

create a natal chart

First Name: John
Last Name: Doe
Date of Birth: 15-08-1985 11:50
Place of Birth: New York, NY, USA

-- 
Best regards""",
            'MessageID': 'test-message-id',
            'Attachments': []
        }

        # Mock transformer responses
        mock_responses = {
            "What is the first name?": {"answer": "John"},
            "What is the last name?": {"answer": "Doe"},
            "What is the date of birth?": {"answer": "15-08-1985"},
            "What is the time of birth?": {"answer": "11:50"},
            "Where was the person born?": {"answer": "New York, NY, USA"}
        }
        
        def mock_qa_side_effect(**kwargs):
            return mock_responses[kwargs["question"]]
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(EmailParsingService, '_get_qa_pipeline', return_value=mock_qa):
                parser = EmailParsingService()
                email = parser.parse_webhook_data(mock_webhook_data)
                error = ValidationService.validate_email_for_processing(email)
                assert error is None
                
                user_info = NatalChartService.parse_user_info(email.body)
                assert user_info["First Name"] == "John"
                assert user_info["Last Name"] == "Doe"
                assert user_info["Date of Birth"] == "15-08-1985 11:50"
                assert user_info["Place of Birth"] == "New York, NY, USA"

# Validation Tests
class TestValidation:
    def test_validate_user_info_completeness(self):
        """Test validation of user info completeness."""
        class DummyEmail:
            def __init__(self, body):
                self.body = body
                self.is_ping_request = False
                self.from_email = "test@example.com"

        # Complete info
        body = (
            "First Name: Jane\n"
            "Last Name: Doe\n"
            "Date of Birth: 15-06-1985 08:30\n"
            "Place of Birth: San Francisco, California, USA\n"
        )
        email = DummyEmail(body)
        error = ValidationService.validate_email_for_processing(email)
        assert error is None

        # Missing info
        incomplete_body = (
            "First Name: Jane\n"
            "Date of Birth: 15-06-1985 08:30\n"
        )
        email = DummyEmail(incomplete_body)
        error = ValidationService.validate_email_for_processing(email)
        assert error is not None
        assert error.error_type == 'missing_user_info'

    def test_validation_error_email_formatting(self):
        """Test validation error email formatting."""
        email = IncomingEmail(
            from_email="test@example.com", 
            from_name="John Smith",
            subject="Test",
            body="Only first name: John",
            attachments=[],
            message_id="test123"
        )
        
        error = ValidationError(
            error_type="missing_user_info",
            message="Missing required fields",
            context={}
        )
        
        email_service = EmailService()
        error_content = email_service._create_error_message(email.from_name, error)
        
        assert "<p>" in error_content
        assert "<br>" in error_content  
        assert "Dear John," in error_content
        assert "First Name: ...<br>" in error_content
        assert "Prof. Warlock</p>" in error_content
        
        response = EmailResponse(
            to_email=email.from_email,
            subject="[Prof. Warlock] Missing Information", 
            content=error_content,
            reply_to_message_id=email.message_id
        )
        
        payload = email_service._build_email_payload(response)
        assert "Prof. Warlock <" in payload["From"]
        assert payload["From"].endswith(">")
        assert config.email.FROM_EMAIL in payload["From"]

# Transformer Tests
class TestTransformers:
    def test_parse_with_transformers_standard_format(self):
        """Test transformer parsing with standard formatted input."""
        body = (
            "First Name: Jane\n"
            "Last Name: Doe\n"
            "Date of Birth: 15-06-1985 12:10\n"
            "Place of Birth: San Francisco, California, USA\n"
        )
        
        mock_responses = {
            "What is the first name?": {"answer": "Jane"},
            "What is the last name?": {"answer": "Doe"},
            "What is the date of birth?": {"answer": "15-06-1985 12:10"},
            "Where was the person born?": {"answer": "San Francisco, California, USA"}
        }
        
        def mock_qa_side_effect(**kwargs):
            return mock_responses[kwargs["question"]]
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(NatalChartService, '_get_qa_pipeline', return_value=mock_qa):
                result = NatalChartService._parse_with_transformers(body)
                
                assert result["First Name"] == "Jane"
                assert result["Last Name"] == "Doe"
                assert result["Date of Birth"] == "15-06-1985 12:10"
                assert result["Place of Birth"] == "San Francisco, California, USA"

    def test_parse_with_transformers_unstructured_format(self):
        """Test transformer parsing with unstructured text input."""
        body = """
        Hi Professor,
        
        I would like to get my natal chart. My name is John Smith and I was born 
        in London, England on March 15th, 1990 at 3:45 PM.
        
        Thanks!
        """
        
        mock_responses = {
            "What is the first name?": {"answer": "John"},
            "What is the last name?": {"answer": "Smith"},
            "What is the date of birth?": {"answer": "March 15th, 1990 at 3:45 PM"},
            "Where was the person born?": {"answer": "London, England"}
        }
        
        def mock_qa_side_effect(**kwargs):
            return mock_responses[kwargs["question"]]
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(NatalChartService, '_get_qa_pipeline', return_value=mock_qa):
                result = NatalChartService._parse_with_transformers(body)
                
                assert result["First Name"] == "John"
                assert result["Last Name"] == "Smith"
                assert result["Date of Birth"] == "March 15th, 1990 at 3:45 PM"
                assert result["Place of Birth"] == "London, England"

    def test_parse_with_transformers_error_handling(self):
        """Test error handling in transformer parsing."""
        body = "Some text that should trigger parsing errors"
        
        def mock_qa_side_effect(**kwargs):
            raise Exception("Failed to parse field")
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(NatalChartService, '_get_qa_pipeline', return_value=mock_qa):
                result = NatalChartService._parse_with_transformers(body)
                
                assert result["First Name"] == ""
                assert result["Last Name"] == ""
                assert result["Date of Birth"] == ""
                assert result["Place of Birth"] == ""

    def test_parse_with_transformers_empty_responses(self):
        """Test handling of empty or invalid responses from the transformer."""
        body = "Some text"
        
        mock_responses = {
            "What is the first name?": {"answer": "John Smith"},  # Should only take "John"
            "What is the last name?": {"answer": "   "},  # Empty after strip
            "What is the date of birth?": {"answer": "no date provided"},  # Invalid date
            "Where was the person born?": {"answer": ""}  # Empty string
        }
        
        def mock_qa_side_effect(**kwargs):
            return mock_responses[kwargs["question"]]
        
        mock_qa = MagicMock(side_effect=mock_qa_side_effect)
        
        with patch('transformers.pipeline', return_value=mock_qa):
            with patch.object(NatalChartService, '_get_qa_pipeline', return_value=mock_qa):
                result = NatalChartService._parse_with_transformers(body)
                
                assert result["First Name"] == "John"
                assert result["Last Name"] == ""
                assert result["Date of Birth"] == ""
                assert result["Place of Birth"] == ""

# Chart Generation Tests
class TestChartGeneration:
    def test_zodiac_sign_determination(self):
        """Test zodiac sign determination for different birth dates."""
        test_cases = [
            ("15-03-2000 12:00", "Pisces"),  # March 15
            ("21-03-2000 12:00", "Aries"),   # March 21 - Aries starts
            ("19-04-2000 12:00", "Aries"),   # April 19 - Aries ends
            ("20-04-2000 12:00", "Taurus"),  # April 20 - Taurus starts
            ("22-12-2000 12:00", "Capricorn"),  # December 22 - Capricorn starts
            ("19-01-2000 12:00", "Capricorn"),  # January 19 - Capricorn ends
            ("20-01-2000 12:00", "Aquarius"),   # January 20 - Aquarius starts
        ]

        for date_str, expected_sign in test_cases:
            dt = datetime.strptime(date_str, "%d-%m-%Y %H:%M")
            sign, path = NatalChartService._get_zodiac_sign(dt)
            assert sign == expected_sign
            assert os.path.exists(path)
            assert path.endswith(f"{expected_sign.lower()}.svg")

    def test_chart_generation(self):
        """Test full chart generation with zodiac sign integration."""
        user_info = {
            "First Name": "John",
            "Last Name": "Doe",
            "Date of Birth": "21-03-1990 12:00",  # Aries at noon
            "Place of Birth": "New York, USA"
        }
        
        chart_png = NatalChartService.generate_chart(user_info)
        
        assert chart_png is not None
        assert len(chart_png) > 0
        assert isinstance(chart_png, bytes)
        assert chart_png[:8] == b'\x89PNG\r\n\x1a\n'  # PNG signature

        # Save output for manual inspection
        os.makedirs("test_results", exist_ok=True)
        with open("test_results/test_chart_generation.png", "wb") as f:
            f.write(chart_png)

    def test_chart_generation_with_different_signs(self):
        """Test chart generation with different zodiac signs."""
        test_locations = [
            "New York, USA",
            "London, UK",
            "Tokyo, Japan",
            "Sydney, Australia"
        ]
        
        test_dates = [
            "21-03-1990 12:00",  # Aries at noon
            "21-06-1990 12:00",  # Cancer at noon
            "23-09-1990 12:00",  # Libra at noon
            "22-12-1990 12:00",  # Capricorn at noon
        ]
        
        for date, location in zip(test_dates, test_locations):
            user_info = {
                "First Name": "Test",
                "Last Name": "User",
                "Date of Birth": date,
                "Place of Birth": location
            }
            
            chart_png = NatalChartService.generate_chart(user_info)
            
            assert chart_png is not None
            assert len(chart_png) > 0
            assert isinstance(chart_png, bytes)

    def test_invalid_date_format(self):
        """Test error handling for invalid date format."""
        user_info = {
            "First Name": "John",
            "Last Name": "Doe",
            "Date of Birth": "invalid-date",
            "Place of Birth": "New York, USA"
        }
        
        with pytest.raises(ValueError, match="Date of Birth must be in DD-MM-YYYY HH:MM format"):
            NatalChartService.generate_chart(user_info)

    def test_invalid_location(self):
        """Test error handling for invalid location."""
        user_info = {
            "First Name": "John",
            "Last Name": "Doe",
            "Date of Birth": "21-03-1990 12:00",
            "Place of Birth": "NonexistentPlace, NowhereCountry"
        }
        
        with pytest.raises(ValueError, match="Could not geocode location"):
            NatalChartService.generate_chart(user_info)

# API Tests
class TestAPI:
    def test_health_check_root(self):
        """Test root health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Prof. Warlock" in data["message"]

    def test_health_check_detailed(self):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Prof. Warlock"
        assert "features" in data

    def test_webhook_ping_pong(self):
        """Test webhook ping/pong functionality."""
        webhook_data = {
            'From': 'test@example.com',
            'FromName': 'Test User',
            'Subject': 'ping',
            'TextBody': 'ping',
            'Attachments': []
        }
        token = config.security.WEBHOOK_SECRET_TOKEN
        response = client.post(f"/webhook?token={token}", json=webhook_data)
        
        assert response.status_code in [200, 500]
        data = response.json()
        assert "action" in data
        assert data["action"] == "pong_sent" 