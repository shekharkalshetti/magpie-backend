"""
FastAPI entrypoint for the Triton control plane.

DEPRECATED: This file is kept for backward compatibility.
The new entry point is src/main.py.

For new development, use:
    uvicorn src.main:app --reload

This file re-exports the app from src.main for backward compatibility
with existing deployments that import from backend.main.
"""
# Re-export everything from new structure for backward compatibility
from src.main import app

# Keep backward compatible imports working
from src.config import settings


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
