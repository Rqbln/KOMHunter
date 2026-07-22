"""
KOMHunter FastAPI Application Entry Point.

This is the main entry point for the KOMHunter API server.
It configures middleware, routes, and exception handlers.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.routes import auth, segments, athletes, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    print("Shutting down KOMHunter API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API for discovering and analyzing Strava segments to hunt KOMs",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Let the browser read the transparently-refreshed session token
        expose_headers=["X-KOM-Refreshed-Token"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(athletes.router, prefix="/api/athletes", tags=["Athletes"])
    app.include_router(segments.router, prefix="/api/segments", tags=["Segments"])
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint redirects to documentation."""
        return JSONResponse(
            content={
                "message": "Welcome to KOMHunter API",
                "docs": "/docs",
                "health": "/api/health",
            }
        )
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
