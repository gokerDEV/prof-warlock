"""
AI analysis service for generating feedback.

Handles communication with OpenAI Chat Completions API for getting annotation script.
"""

import base64
import os
import io
from typing import Optional, Tuple
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv
import logging

from ..core.domain_models import ProcessedImage, AIAnalysisResult, IncomingEmail
from .image_annotation.annotator import ImageAnnotator

# Load .env for OPENAI_API_KEY
load_dotenv()

class AIAnalysisService:
    """Service for AI-powered content analysis and feedback generation (Chat Completions API)."""
    def __init__(self):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.instructions = self._load_instructions()
    
    def encode_image(self, image_path):
        """Encode image as base64 for OpenAI API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _load_instructions(self) -> str:
        instructions_path = os.path.join(os.path.dirname(__file__), '../../assets/instructions.txt')
        instructions_path = os.path.abspath(instructions_path)
        if not os.path.exists(instructions_path):
            raise FileNotFoundError(f"Instructions file not found: {instructions_path}")
        with open(instructions_path, "r") as f:
            return f.read()

    def analyze_submission(self, email: IncomingEmail, processed_image: ProcessedImage) -> AIAnalysisResult:
        """
        Get annotation script from OpenAI Chat Completions API and execute it.
        Args:
            email: The incoming email with submission details
            processed_image: Processed image for analysis
        Returns:
            AIAnalysisResult: Analysis result with feedback and annotated image
        """
        import tempfile
        import os
        
        # Create temporary file for the scaled image
        temp_dir = tempfile.mkdtemp()
        temp_image_path = os.path.join(temp_dir, 'temp_image.jpg')
        
        try:
            # Write scaled image to temporary file
            if processed_image.scaled_content:
                with open(temp_image_path, 'wb') as f:
                    f.write(processed_image.scaled_content)
                logging.info(f"Scaled image saved to temp file: {temp_image_path}, size: {len(processed_image.scaled_content)} bytes")
            else:
                raise Exception("No scaled content available for processing")

            # Prepare image as base64 from temp file
            base64_image = self.encode_image(temp_image_path)

            # Prepare prompt
            prompt = f"Score this photo. Student message: \"{email.body}\""

            # Call OpenAI Chat Completions API with proper format
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self.instructions
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                        ],
                    }
                ],
                max_tokens=4000
            )

            response_text = response.choices[0].message.content
            if not response_text:
                raise Exception("No response received from OpenAI")

            logging.debug(f"OpenAI Response received: length={len(response_text)}; preview={response_text[:200]}")
            if "```python" in response_text:
                logging.info("Python code block found in response")
            else:
                logging.warning("No Python code block found in response")

            # Extract feedback and code
            feedback_text, python_code = self._extract_feedback_and_code(response_text)
            
            # Save extracted code for debugging
            if python_code:
                logging.debug("Python code extracted from OpenAI response.")
            else:
                logging.warning("No Python code to save")
            
            if not python_code:
                logging.error("No Python code extracted from OpenAI response.")
                raise Exception("No Python script received from OpenAI")

            # Execute the annotation script using the same temp file
            annotated_image = self._execute_script(
                temp_image_path,
                python_code,
                None  # scaled_content not needed since we have the file
            )
            if not annotated_image:
                raise Exception("Failed to generate annotated image")

            return AIAnalysisResult(
                feedback_text=feedback_text,
                annotated_image=annotated_image,
                analysis_type="image_with_annotation"
            )
        except Exception as e:
            logging.error(f"AI ANALYSIS ERROR: {str(e)}", exc_info=True)
            return AIAnalysisResult(
                feedback_text=self._create_error_response(email, str(e)),
                analysis_type="error"
            )
        finally:
            # Cleanup temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                logging.debug(f"Cleaned up temp directory: {temp_dir}")
            except:
                pass

    def _extract_feedback_and_code(self, response_text: str) -> Tuple[str, Optional[str]]:
        """Extract feedback text and Python code from AI response."""
        import re
        code_pattern = r'```python\s*\n(.*?)\n```'
        code_matches = re.findall(code_pattern, response_text, re.DOTALL)
        feedback_text = re.sub(code_pattern, '', response_text, flags=re.DOTALL).strip()
        feedback_text = '\n'.join(line.strip() for line in feedback_text.split('\n') if line.strip())
        python_code = code_matches[0] if code_matches else None
        return feedback_text, python_code

    def _execute_script(self, image_path: str, python_code: str, scaled_content: Optional[bytes] = None) -> Optional[bytes]:
        """
        SECURITY WARNING: This method executes arbitrary Python code received from OpenAI.
        This is extremely dangerous and should only be used in a secure, sandboxed environment.
        For production or open source, use a proper sandbox or restrict code execution.
        """
        try:
            import tempfile
            import shutil
            
            # Create a temporary copy of the image with the expected name
            temp_dir = tempfile.mkdtemp()
            temp_image_path = os.path.join(temp_dir, 'temp_image.jpg')
            
            # Use scaled content if available, otherwise original file
            if scaled_content:
                logging.info("Using scaled image content for annotation")
                with open(temp_image_path, 'wb') as f:
                    f.write(scaled_content)
            else:
                logging.info("Using original image file")
                shutil.copy2(image_path, temp_image_path)
            
            # Also create the annotated output path
            annotated_output_path = os.path.join(temp_dir, 'annotated_output.jpg')
            
            # Change working directory temporarily for the script execution
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                image = Image.open(temp_image_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                annotator = ImageAnnotator(image)
                exec_context = {
                    'Image': Image,
                    'ImageAnnotator': ImageAnnotator,
                    'annotator': annotator,
                    'image': image
                }
                # WARNING: Executing code from OpenAI is dangerous! This should be sandboxed in production/open source.
                logging.warning("Executing code from OpenAI response. This is dangerous and should be sandboxed in production.")
                exec(python_code, exec_context)
                
                # Check if annotated_output.jpg was created
                if os.path.exists(annotated_output_path):
                    with open(annotated_output_path, 'rb') as f:
                        result_bytes = f.read()
                    return result_bytes
                else:
                    # Fallback: use annotator's save_image method
                    final_image = annotator.save_image(annotated_output_path)
                    with open(annotated_output_path, 'rb') as f:
                        result_bytes = f.read()
                    return result_bytes
                    
            finally:
                # Restore working directory and cleanup
                os.chdir(original_cwd)
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logging.error(f"Script execution failed: {e}", exc_info=True)
            return None

    def _create_error_response(self, email: IncomingEmail, error_msg: str) -> str:
        """Create an error response when something fails."""
        first_name = email.from_name.split()[0] if email.from_name else "Student"
        return f"""Dear {first_name},\n\nI apologize, but I encountered a technical issue while analyzing your photo. Please try submitting again. If the problem persists, please contact support.\n\nBest regards,\nProf. Postmark\n\n(Error: {error_msg[:100]}...)""" 