import os
import base64
from unittest.mock import patch
from src.core.domain_models import EmailAttachment, ProcessedImage
from src.services.email_parser import EmailParsingService
from src.services.image_processor import ImageProcessingService
from PIL import Image
from src.api.webhook_handler import WebhookHandler
import pytest
from src.services.validation_service import ValidationService
from src.services.ai_analysis_service import AIAnalysisService

TEST_IMAGE_PATH = "assets/test.jpeg"
TEST_OUTPUT_DIR = "test_results"

def setup_test_dirs():
    """Ensure test directories exist."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

def create_test_attachment_from_file(image_path: str, name: str = "test.jpeg") -> EmailAttachment:
    with open(image_path, "rb") as f:
        img_data = f.read()
    return EmailAttachment(
        name=name,
        content_type="image/jpeg",
        content_length=len(img_data),
        content=img_data
    )

def get_test_image_data_and_b64():
    with open(TEST_IMAGE_PATH, "rb") as f:
        img_data = f.read()
    img_b64 = base64.b64encode(img_data).decode("utf-8")
    return img_data, img_b64

class TestSystem:
    def test_parse_email_with_attachment(self):
        """Test parsing email with attachment."""
        img_data, img_b64 = get_test_image_data_and_b64()
        webhook_data = {
            'From': 'student@example.com',
            'FromName': 'Jane Student',
            'Subject': 'Photo submission',
            'TextBody': 'Here is my photo',
            'Attachments': [{
                'Name': 'photo.jpg',
                'ContentType': 'image/jpeg',
                'ContentLength': len(img_data),
                'Content': img_b64
            }]
        }
        email = EmailParsingService.parse_webhook_data(webhook_data)
        assert len(email.attachments) == 1
        assert email.attachments[0].name == 'photo.jpg'
        assert email.attachments[0].content_type == 'image/jpeg'
        assert len(email.attachments[0].content) > 0

    def test_process_square_image(self):
        """Test processing of square image (center crop 800x800)."""
        # Crop center 800x800 from original image
        with Image.open(TEST_IMAGE_PATH) as img:
            width, height = img.size
            left = (width - 800) // 2
            top = (height - 800) // 2
            right = left + 800
            bottom = top + 800
            img_cropped = img.crop((left, top, right, bottom))
            square_path = os.path.join(TEST_OUTPUT_DIR, "square_test.jpg")
            img_cropped.save(square_path)
        with open(square_path, "rb") as f:
            img_data = f.read()
        attachment = EmailAttachment(
            name='square.jpg',
            content_type='image/jpeg',
            content_length=len(img_data),
            content=img_data
        )
        processed = ImageProcessingService.process_image_attachment(attachment)
        processed_image = ProcessedImage(
            image_path=square_path,
            width=processed.width,
            height=processed.height,
            original_filename=attachment.name,
            content_type=attachment.content_type,
            scaled_content=processed.scaled_content
        )
        assert processed_image.width > 0
        assert processed_image.height > 0
        assert abs(processed_image.width - processed_image.height) < 10  # Should be square

    def test_process_landscape_image(self):
        """Test processing of landscape image (original)."""
        img_data, _ = get_test_image_data_and_b64()
        attachment = EmailAttachment(
            name='landscape.jpg',
            content_type='image/jpeg',
            content_length=len(img_data),
            content=img_data
        )
        processed = ImageProcessingService.process_image_attachment(attachment)
        processed_image = ProcessedImage(
            image_path=TEST_IMAGE_PATH,
            width=processed.width,
            height=processed.height,
            original_filename=attachment.name,
            content_type=attachment.content_type,
            scaled_content=processed.scaled_content
        )
        assert processed_image.width > processed_image.height  # Should be landscape

    def test_process_portrait_image(self):
        """Test processing of portrait image (rotated 90 degrees)."""
        # Rotate original image 90 degrees
        with Image.open(TEST_IMAGE_PATH) as img:
            img_rotated = img.rotate(90, expand=True)
            portrait_path = os.path.join(TEST_OUTPUT_DIR, "portrait_test.jpg")
            img_rotated.save(portrait_path)
        with open(portrait_path, "rb") as f:
            img_data = f.read()
        attachment = EmailAttachment(
            name='portrait.jpg',
            content_type='image/jpeg',
            content_length=len(img_data),
            content=img_data
        )
        processed = ImageProcessingService.process_image_attachment(attachment)
        processed_image = ProcessedImage(
            image_path=portrait_path,
            width=processed.width,
            height=processed.height,
            original_filename=attachment.name,
            content_type=attachment.content_type,
            scaled_content=processed.scaled_content
        )
        assert processed_image.height > processed_image.width  # Should be portrait

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test the complete workflow from email to annotated image."""
        webhook_handler = WebhookHandler()
        img_data, img_b64 = get_test_image_data_and_b64()
        webhook_data = {
            'From': 'student@example.com',
            'FromName': 'Test Student',
            'Subject': 'Score my photo',
            'TextBody': 'Please score this photo',
            'Attachments': [{
                'Name': 'photo.jpg',
                'ContentType': 'image/jpeg',
                'ContentLength': len(img_data),
                'Content': img_b64
            }]
        }
        # Mock email service to avoid actual sending
        with patch.object(webhook_handler.email_service, 'send_feedback_response', return_value=True):
            result = await webhook_handler.process_webhook(webhook_data)
        assert result['status'] == 'success'
        assert 'feedback_sent' in result['action']

    def test_validate_valid_attachment(self):
        """Test validation of a valid attachment."""
        attachment = EmailAttachment(
            name='test.jpg',
            content_type='image/jpeg',
            content_length=1024,  # 1KB
            content=b'fake_image_data'
        )
        error = ValidationService.validate_attachment(attachment)
        assert error is None

    def test_validate_oversized_attachment(self):
        """Test validation of oversized attachment."""
        attachment = EmailAttachment(
            name='large.jpg',
            content_type='image/jpeg',
            content_length=10 * 1024 * 1024,  # 10MB
            content=b'fake_large_data'
        )
        error = ValidationService.validate_attachment(attachment)
        assert error is not None
        assert error.error_type == 'file_too_large'

    def test_validate_invalid_file_type(self):
        """Test validation of invalid file type."""
        attachment = EmailAttachment(
            name='document.pdf',
            content_type='application/pdf',
            content_length=1024,
            content=b'fake_pdf_data'
        )
        error = ValidationService.validate_attachment(attachment)
        assert error is not None
        assert error.error_type == 'invalid_file_type'

    @pytest.mark.skipif(os.environ.get("OPENAI_API_KEY") is None, reason="OPENAI_API_KEY not set")
    def test_openai_script_generation(self):
        """Test real OpenAI call: request script, check feedback and code."""
        ai_service = AIAnalysisService()
        attachment = create_test_attachment_from_file(TEST_IMAGE_PATH)
        email = EmailParsingService.parse_webhook_data({
            'From': 'student@example.com',
            'FromName': 'Test Student',
            'Subject': 'Score my photo',
            'TextBody': 'Please score this photo',
            'Attachments': [{
                'Name': 'photo.jpg',
                'ContentType': 'image/jpeg',
                'ContentLength': attachment.content_length,
                'Content': base64.b64encode(attachment.content).decode('utf-8')
            }]
        })
        processed = ImageProcessingService.process_image_attachment(attachment)
        processed_image = ProcessedImage(
            image_path=TEST_IMAGE_PATH,
            width=processed.width,
            height=processed.height,
            original_filename=attachment.name,
            content_type=attachment.content_type,
            scaled_content=processed.scaled_content
        )
        result = ai_service.analyze_submission(email, processed_image)
        
        # Test expectations
        assert result.feedback_text, "No feedback received"
        assert "Score:" in result.feedback_text, "No score found in feedback"
        assert result.annotated_image is not None, "No annotated image generated"
        assert result.analysis_type == "image_with_annotation", f"Wrong analysis type: {result.analysis_type}" 