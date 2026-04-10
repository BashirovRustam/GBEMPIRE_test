"""
Vercel serverless entry point for FastAPI application
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from mangum import Mangum

# Vercel serverless handler using Mangum ASGI adapter
handler = Mangum(app)
