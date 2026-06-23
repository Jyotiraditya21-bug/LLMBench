from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.app.core.config import settings
from backend.app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Include core API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Setup CORS (Cross-Origin Resource Sharing) permissions
# Essential when frontend and backend run on different container ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for SPA assets under /dashboard/static
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/dashboard/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    """Serve the Single Page Application (SPA) dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
async def health_check():
    """Detailed health check endpoint for container probes."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
    }

