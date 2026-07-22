"""
Health check endpoints for monitoring and load balancers.
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns the current status of the API server including
    version information and timestamp.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check for Kubernetes/Docker health probes.
    
    Verifies that the application is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes/Docker health probes.
    
    Verifies that the application is still running.
    """
    return {"status": "alive"}
