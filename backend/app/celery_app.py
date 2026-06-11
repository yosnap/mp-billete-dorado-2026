from celery import Celery

from app.core.config import get_settings
from app.domains.notifications.beat_schedule import NOTIFICATIONS_BEAT_SCHEDULE

settings = get_settings()

celery_app = Celery(
    "mp_billete_dorado",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.domains.notifications.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Schedules de campaña: last_chance (23-sep) y grand_final (30-sep)
    beat_schedule=NOTIFICATIONS_BEAT_SCHEDULE,
)
