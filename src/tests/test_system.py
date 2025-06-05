import os
import base64
from src.services.email_parser import EmailParsingService
from src.services.validation_service import ValidationService
from src.services.natal_chart_service import NatalChartService
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.configuration import config
import json
import re

def test_parse_email_with_user_info():
    # Strict input format, no image, just user info
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
    email = EmailParsingService.parse_webhook_data(webhook_data)
    assert email.body.strip() == body.strip()
    for field in ["First Name:", "Last Name:", "Date of Birth:", "Place of Birth:"]:
        assert field in email.body
    assert email.from_email == 'jane.doe@example.com'
    assert email.from_name == 'Jane Doe'
    assert email.attachments == []

def test_validate_user_info_completeness():
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

def test_natal_chart_creation():
    user_info = {
        "First Name": "Jane",
        "Last Name": "Doe",
        "Date of Birth": "15-06-1985 14:30",
        "Place of Birth": "San Francisco, California, USA"
    }
    chart_bytes = NatalChartService.generate_chart(user_info)
    assert isinstance(chart_bytes, bytes)
    assert chart_bytes[:8] == b'\x89PNG\r\n\x1a\n'  # PNG file signature
    # Save the PNG for manual inspection
    os.makedirs("test_results", exist_ok=True)
    with open("test_results/natal_chart_test.png", "wb") as f:
        f.write(chart_bytes)

client = TestClient(app)

def test_health_check_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Prof. Warlock" in data["message"]

def test_health_check_detailed():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Prof. Warlock"
    assert "features" in data

def test_webhook_ping_pong():
    """Test webhook ping/pong functionality without sending actual emails."""
    # Use a mock email that won't trigger Postmark sending
    webhook_data = {
        'From': 'test@example.com',
        'FromName': 'Test User',
        'Subject': 'ping',
        'TextBody': 'ping',
        'Attachments': []
    }
    token = config.security.WEBHOOK_SECRET_TOKEN
    response = client.post(f"/webhook?token={token}", json=webhook_data)
    
    # The webhook processing works even if email sending fails
    assert response.status_code in [200, 500]
    
    # Parse the JSON response
    data = response.json()
    
    # The webhook should recognize the ping and attempt to send a pong
    assert "action" in data
    assert data["action"] == "pong_sent"
    
    # In test environment, email sending might fail, which is expected
    if response.status_code == 500:
        assert data["status"] == "error"
        assert "failed" in data["message"].lower() or "pong" in data["message"].lower()
    else:
        assert data["status"] == "success"

def test_inbound_email_parsing_with_mock_data():
    """Test email parsing with mock inbound email data."""
    # Create mock webhook data similar to real Postmark payload
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
    
    # Parse the email
    email = EmailParsingService.parse_webhook_data(mock_webhook_data)
    
    # Should pass validation
    error = ValidationService.validate_email_for_processing(email)
    assert error is None
    
    # Should successfully parse user info
    user_info = NatalChartService.parse_user_info(email.body)
    assert user_info["First Name"] == "John"
    assert user_info["Last Name"] == "Doe"
    assert user_info["Date of Birth"] == "15-08-1985 11:50"
    assert user_info["Place of Birth"] == "New York, NY, USA"

def test_end_to_end_natal_chart_with_mock():
    """Test the complete end-to-end natal chart generation workflow with mock data."""
    # Create mock email data with proper formatting for parsing
    mock_webhook_data = {
        'From': 'test@example.com',
        'FromName': 'Test User',
        'Subject': 'natal chart request',
        'TextBody': """First Name: Alice
Last Name: Smith
Date of Birth: 15-03-1985 12:10
Place of Birth: London, UK

Please create my natal chart. Thank you!""",
        'MessageID': 'test-message-id',
        'Attachments': []
    }
    
    # Parse the email
    email = EmailParsingService.parse_webhook_data(mock_webhook_data)
    
    # Extract user info
    user_info = NatalChartService.parse_user_info(email.body)
    assert user_info["First Name"] == "Alice"
    assert user_info["Last Name"] == "Smith"
    assert user_info["Date of Birth"] == "15-03-1985 12:10"
    assert user_info["Place of Birth"] == "London, UK"
    
    # Generate natal chart
    chart_bytes = NatalChartService.generate_chart(user_info)
    assert len(chart_bytes) > 0
    assert isinstance(chart_bytes, bytes)
    assert chart_bytes[:8] == b'\x89PNG\r\n\x1a\n'  # PNG file signature
    
    # Save the chart for manual inspection
    with open("test_end_to_end_chart.png", "wb") as f:
        f.write(chart_bytes)

def test_validation_error_email_formatting():
    """Test that validation error emails have proper formatting and sender info."""
    from src.core.domain_models import IncomingEmail, ValidationError
    from src.services.email_service import EmailService
    
    # Create a test email with missing info
    email = IncomingEmail(
        from_email="test@example.com", 
        from_name="John Smith",
        subject="Test",
        body="Only first name: John",
        attachments=[],
        message_id="test123"
    )
    
    # Create validation error
    error = ValidationError(
        error_type="missing_user_info",
        message="Missing required fields",
        context={}
    )
    
    # Test the error message formatting
    email_service = EmailService()
    error_content = email_service._create_error_message(email.from_name, error)
    
    # Verify HTML formatting
    assert "<p>" in error_content
    assert "<br>" in error_content  
    assert "Dear John," in error_content  # Name extraction (properly capitalized)
    assert "First Name: ...<br>" in error_content
    assert "Prof. Warlock</p>" in error_content
    
    # Test payload building
    from src.core.domain_models import EmailResponse
    response = EmailResponse(
        to_email=email.from_email,
        subject="[Prof. Warlock] Missing Information", 
        content=error_content,
        reply_to_message_id=email.message_id
    )
    
    payload = email_service._build_email_payload(response)
    
    # Verify sender format
    assert "Prof. Warlock <" in payload["From"]
    assert payload["From"].endswith(">")
    assert config.email.FROM_EMAIL in payload["From"] 