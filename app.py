"""
Prof. Postmark Application Entry Point

Clean entry point for running the FastAPI application.
"""

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 