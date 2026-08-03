from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "evalforge_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.app.workers.tasks",
        "backend.app.workers.agent_tasks",
    ],
)

# Optimize Celery worker configs
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Avoid prefetching tasks to distribute load evenly across workers
    worker_prefetch_multiplier=1,
)
