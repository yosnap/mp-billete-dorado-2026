"""
Tareas Celery para el envío asíncrono de emails.

Cada tarea usa autoretry_for con backoff exponencial (máx 3 reintentos).
El rate limit de 100 emails/min se controla a nivel de worker con
rate_limit="100/m" en la definición de la tarea.
"""
import logging
import uuid
from typing import Any

from celery import shared_task

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="notifications.send_notification",
    # Máx 100 emails por minuto por worker — evita triggering de spam filters
    rate_limit="100/m",
    # Reintentos automáticos ante cualquier excepción, backoff exponencial
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,  # 5 min máximo entre reintentos
    retry_jitter=True,
    # El worker confirma el mensaje solo tras éxito o max_retries agotados
    acks_late=True,
)
def send_notification(
    self,
    participant_id: str,
    email_type: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Envía un email de notificación de forma asíncrona.

    Args:
        participant_id: UUID del participante como string.
        email_type: Tipo de email (welcome, winner, no_prize, etc.)
        context: Diccionario de variables de contexto para la plantilla.

    Returns:
        dict con participant_id, email_type y status del envío.
    """
    import asyncio

    from app.domains.notifications.service import send_email

    pid = uuid.UUID(participant_id)
    ctx = context or {}

    logger.info(
        "send_notification task_id=%s participant=%s type=%s attempt=%d",
        self.request.id,
        participant_id[:8],
        email_type,
        self.request.retries + 1,
    )

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            await send_email(db, pid, email_type, ctx)

    asyncio.run(_run())

    return {
        "participant_id": participant_id,
        "email_type": email_type,
        "status": "sent",
        "attempt": self.request.retries + 1,
    }


@shared_task(
    name="notifications.send_bulk_campaign",
    rate_limit="10/m",
    acks_late=True,
)
def send_bulk_campaign(
    email_type: str,
    context: dict[str, Any] | None = None,
    participant_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Encola tareas individuales para un envío masivo de campaña.

    Si participant_ids es None, envía a todos los participantes con
    consent_marketing=True. Cada envío individual es una tarea separada
    para que los reintentos sean por participante, no globales.
    """
    import asyncio

    from sqlalchemy import select

    from app.domains.participants.models import Participant

    ctx = context or {}
    queued = 0
    errors = 0

    async def _fetch_participants() -> list[str]:
        async with AsyncSessionLocal() as db:
            if participant_ids:
                return [str(pid) for pid in participant_ids]

            result = await db.execute(
                select(Participant.id).where(
                    Participant.consent_marketing.is_(True)
                )
            )
            return [str(row[0]) for row in result.fetchall()]

    pids = asyncio.run(_fetch_participants())

    for pid_str in pids:
        try:
            send_notification.delay(pid_str, email_type, ctx)
            queued += 1
        except Exception as exc:
            logger.error(
                "bulk_campaign enqueue_failed participant=%s type=%s error=%s",
                pid_str[:8],
                email_type,
                str(exc)[:100],
            )
            errors += 1

    logger.info(
        "bulk_campaign type=%s queued=%d errors=%d",
        email_type,
        queued,
        errors,
    )
    return {"email_type": email_type, "queued": queued, "errors": errors}
