from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mp_billete_dorado",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        # Los tasks se registran aquí conforme se crean en fases posteriores
        # "app.tasks.notifications",  # Phase-05
        # "app.tasks.prizes",         # Phase-03
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
)
