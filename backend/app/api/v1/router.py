from fastapi import APIRouter

from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.prompts import router as prompts_router
from backend.app.api.v1.evaluations import router as evaluations_router
from backend.app.api.v1.agents import router as agents_router

api_router = APIRouter(redirect_slashes=False)

api_router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
api_router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
api_router.include_router(evaluations_router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
