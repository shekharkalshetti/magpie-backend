"""
FastAPI entrypoint for the Triton control plane.

This is the main application that handles:
- Project management
- Metadata key configuration
- Execution log ingestion
- User authentication and team management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models first to ensure SQLAlchemy can resolve relationships
from src import models  # noqa: F401
from src.auth.middleware import ApiKeyMiddleware
from src.config import settings
from src.constants import SHOW_DOCS_ENVIRONMENTS
from src.database import create_tables
from src.audit_logs.router import router as audit_logs_router
from src.logs.router import router as logs_router
from src.policies.router import router as policies_router
from src.projects.router import router as projects_router
from src.review_queue.router import router as review_queue_router
from src.users.router import router as auth_router
from src.users.team_router import router as team_router

# Configure app based on environment
app_configs = {
    "title": "Triton Control Plane",
    "description": "Enterprise-grade LLM middleware platform",
    "version": settings.APP_VERSION,
}

# Hide docs in production (unless explicitly enabled)
if settings.ENVIRONMENT not in SHOW_DOCS_ENVIRONMENTS:
    app_configs["openapi_url"] = None

app = FastAPI(**app_configs)

# API Key authentication middleware
app.add_middleware(ApiKeyMiddleware)

# CORS middleware (must be after auth middleware in code but executes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or [
        "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup


@app.on_event("startup")
async def startup_event():
    """Create all database tables on application startup."""
    create_tables()

# Register routes
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    team_router,
    prefix="/api/v1/projects",
    tags=["Team Management"],
)
app.include_router(
    projects_router,
    prefix="/api/v1/projects",
    tags=["Projects"],
)
app.include_router(
    audit_logs_router,
    prefix="/api/v1",
    tags=["Audit Logs"],
)
app.include_router(
    logs_router,
    prefix="/api/v1/logs",
    tags=["Logs"],
)
app.include_router(
    policies_router,
    prefix="/api/v1/policies",
    tags=["Policies"],
)
app.include_router(
    review_queue_router,
    prefix="/api/v1",
    tags=["Review Queue"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "triton-control-plane"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected",  # TODO: Add actual DB health check
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
