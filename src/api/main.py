"""
FastAPI application for Prof. Warlock.

Clean, focused API with proper error handling and security.
"""

import logging
from fastapi import FastAPI, HTTPException, Request, Query, Depends, Header
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from datetime import datetime
import base64
from PIL import Image
import io
import boto3
from hashlib import sha256

from .. import __version__

from ..core.configuration import config
from ..core.domain_models import NatalChartRequest, NatalStatsRequest
from .webhook_handler import WebhookHandler
from ..services.natal_chart_service import NatalChartService

APP_VERSION = __version__


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Prof. Warlock",
    description="Natal Chart Poster Generator via Email",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services
webhook_handler = WebhookHandler()
natal_chart_service = NatalChartService()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=config.s3.REGION,
    aws_access_key_id=config.s3.ACCESS_KEY_ID,
    aws_secret_access_key=config.s3.SECRET_ACCESS_KEY
)


def verify_webhook_token(token: Optional[str] = Query(None)) -> str:
    """
    Verify webhook authentication token.
    
    Args:
        token: Token from query parameter
        
    Returns:
        str: Verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not token or token != config.security.WEBHOOK_SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing webhook token"
        )
    return token


async def verify_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> str:
    """
    Verify API key from header.
    
    Args:
        x_api_key: API key from X-Api-Key header
        
    Returns:
        str: Verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key or x_api_key != config.security.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing API key"
        )
    return x_api_key


@app.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "message": "Prof. Warlock is running!",
        "status": "healthy",
        "version": APP_VERSION
    }


@app.get("/health")
async def detailed_health_check():
    """Detailed health check with system information."""
    return {
        "status": "healthy",
        "service": "Prof. Warlock",
        "version": APP_VERSION,
        "features": [
            "email_parsing",
            "image_processing",
            "personalized_responses"
        ]
    }


@app.post("/webhook")
async def process_email_webhook(
    request: Request,
    token: str = Depends(verify_webhook_token)
):
    """
    Process incoming email webhooks from Postmark.
    
    Complete Email-to-AI-to-Email Workflow:
    1. Security validation (webhook token)
    2. Email parsing and cleaning
    3. PING/PONG health check handling
    4. Natal chart generation    
    5. Personalized email response
    
    Security: Requires valid token parameter for authentication.
    Usage: POST /webhook?token=your-secret-token
    """
    try:
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"📧 Received webhook from: {webhook_data.get('From', 'unknown')}")
        
        # Process through webhook handler
        result = await webhook_handler.process_webhook(webhook_data)
        
        # Return appropriate response
        if result["status"] == "success":
            return JSONResponse(content=result, status_code=200)
        elif result["status"] == "partial_success":
            return JSONResponse(content=result, status_code=202)  # Accepted
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"💥 Webhook endpoint error: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Webhook processing failed: {str(e)}"
            },
            status_code=500
        )


@app.post("/natal-chart")
async def generate_natal_chart(
    request: NatalChartRequest,
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Generate a natal chart based on birth information.
    
    Args:
        request: Birth information for natal chart generation
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Generated natal chart data and image
    """
    try:
        user_info = {
            "First Name": request.first_name,
            "Last Name": request.last_name,
            "Date of Birth": f"{request.birth_day}-{request.birth_month}-{request.birth_year} {request.birth_time}",
            "Place of Birth": request.birth_place,
            "Latitude": request.latitude,
            "Longitude": request.longitude
        }

        # Generate natal chart
        chart_data_bytes = natal_chart_service.generate_chart(user_info)

        # Resize image
        image = Image.open(io.BytesIO(chart_data_bytes))
        max_size = 1500
        image.thumbnail((max_size, max_size), Image.LANCZOS)

        # Save image to bytes
        output = io.BytesIO()
        image.save(output, format='PNG')
        resized_chart_data_bytes = output.getvalue()

        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_digest = sha256(resized_chart_data_bytes).hexdigest()[:8]
        filename = f"natal_charts/{timestamp}_{hash_digest}.png"

        # Upload to S3
        s3_client.put_object(
            Bucket=config.s3.BUCKET,
            Key=filename,
            Body=resized_chart_data_bytes,
            ContentType='image/png'
        )

        # Generate download link
        download_link = f"{config.s3.PUBLIC_URL}{filename}"

        return JSONResponse(content=[{
            "name": "natal_chart.png",
            "id": filename,
            "mime_type": "image/png",
            "download_link": download_link
        }])
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"Failed to generate natal chart: {str(e)}"
        }, status_code=500)


@app.post("/natal-stats")
async def get_natal_stats(
    request: NatalStatsRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Get natal stats including sun sign, moon sign, rising sign and transit information.
    
    Args:
        request: Birth information and optional today's date and time
        api_key: API key for authentication
        
    Returns:
        Dict: Natal stats and transit information
    """
    try:
        # Get natal stats
        stats = await natal_chart_service.get_natal_stats(
            birth_datetime=f"{request.birth_day}-{request.birth_month}-{request.birth_year} {request.birth_time}",
            birth_place=request.birth_place,
            latitude=request.latitude,
            longitude=request.longitude,
            today_date=f"{request.today_day}-{request.today_month}-{request.today_year}",
            today_time=request.today_time
        )
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get natal stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal stats: {str(e)}"
        )


@app.get("/privacy")
async def privacy_policy():
    """Endpoint to provide information about data privacy."""
    return "This system does not store any data. It processes the provided information to generate insights and returns the results without retaining any data."


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"💥 Unhandled exception: {str(exc)}")
    return JSONResponse(
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc)
        },
        status_code=500
    ) 