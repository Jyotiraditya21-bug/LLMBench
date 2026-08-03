import asyncio
import logging
import os
import time
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from redis import asyncio as async_redis
from sqlalchemy import text

from backend.app.api.v1.router import api_router
from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.core.database import async_session_maker


logger = logging.getLogger("llmbench.api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)
app.include_router(api_router, prefix=settings.API_V1_STR)

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=[settings.API_KEY_NAME, "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1_000,
    )
    return response


static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/dashboard/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    """Serve the Single Page Application dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
@app.get("/health/live")
async def liveness_check():
    """Process-level probe that does not depend on downstream services."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get("/health/ready")
async def readiness_check():
    """Verify the database, queue, and worker before accepting traffic."""
    components = {"database": False, "redis": False, "worker": False}

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        components["database"] = True
    except Exception:
        logger.exception("readiness_database_failed")

    redis_client = async_redis.from_url(settings.REDIS_URL)
    try:
        components["redis"] = bool(
            await asyncio.wait_for(redis_client.ping(), timeout=2)
        )
    except Exception:
        logger.exception("readiness_redis_failed")
    finally:
        await redis_client.aclose()

    if settings.READINESS_REQUIRE_WORKER:
        try:
            replies = await asyncio.wait_for(
                asyncio.to_thread(celery_app.control.ping, timeout=1),
                timeout=2,
            )
            components["worker"] = bool(replies)
        except Exception:
            logger.exception("readiness_worker_failed")
    else:
        components["worker"] = True

    ready = all(components.values())
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "ready" if ready else "not_ready",
            "service": settings.PROJECT_NAME,
            "components": components,
        },
    )
