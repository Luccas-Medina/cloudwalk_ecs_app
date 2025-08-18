# app/main.py
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from .logging import init_logging
from .auth import basic_auth
from app.core.config import settings
from dotenv import load_dotenv
import os

# Load variables from .env into environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

init_logging()

app = FastAPI(
    title=settings.app_name + " - Empathic Credit System", 
    version="2.0.0",
    description="CloudWalk Empathic Credit System with Real-time Emotion Processing"
)

# Import and include routers after app is created
from app.api import credit
from app.api.credit import status_router
from app.api import emotion_ws
from app.api import emotion_realtime
from app.api import credit_deployment  # Re-enabled with fixed imports
from app.api import monitoring  # Circuit breaker monitoring
from app.api import privacy_analytics  # Privacy and analytics endpoints

app.include_router(status_router)
app.include_router(credit.router)
app.include_router(credit_deployment.router)  # Credit deployment - re-enabled
app.include_router(monitoring.router)  # Circuit breaker monitoring endpoints
app.include_router(privacy_analytics.router)  # Privacy and analytics endpoints

# Mount the WebSocket routers
app.include_router(emotion_ws.router)  # Legacy emotion WebSocket
app.include_router(emotion_realtime.router)  # Enhanced real-time emotion processing

@app.get("/")
def root():
    return {
        "message": "CloudWalk Empathic Credit System",
        "version": "2.0.0",
        "features": [
            "Real-time emotion processing",
            "Advanced pattern recognition",
            "ML-powered credit decisions", 
            "Multi-source emotion ingestion",
            "Anomaly detection",
            "Risk assessment"
        ],
        "endpoints": {
            "credit": "/api/credit/",
            "emotion_stream": "/ws/emotions/stream",
            "emotion_metrics": "/ws/emotions/metrics",
            "legacy_emotions": "/ws/emotions"
        }
    }

@app.get("/healthz")
def health_check_auth(auth: bool = Depends(basic_auth)):
    return {"status": "ok", "db": "pending", "broker": "pending"}

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}

@app.get("/dashboard", response_class=HTMLResponse)
def emotion_dashboard():
    """Serve the comprehensive real-time emotion processing dashboard"""
    try:
        # Read the comprehensive dashboard HTML file from the app directory
        dashboard_path = os.path.join(os.path.dirname(__file__), "emotion_dashboard.html")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Dashboard Not Found</title></head>
                <body>
                    <h1>Emotion Dashboard Not Found</h1>
                    <p>The comprehensive dashboard file could not be located.</p>
                    <p>Available endpoints:</p>
                    <ul>
                        <li><a href="/docs">API Documentation</a></li>
                        <li><a href="/health">Health Check</a></li>
                    </ul>
                </body>
            </html>
            """,
            status_code=404
        )
