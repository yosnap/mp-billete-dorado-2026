"""
Endpoints admin para el dominio de notificaciones.

Todos los endpoints requieren X-Admin-Token en el header.
Ningún endpoint expone datos personales — solo participant_id y metadatos de envío.
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.notifications.schemas import (
    BulkSendRequest,
    EmailLogResponse,
    SendNotificationRequest,
    SendNotificationResponse,
)
from app.domains.notifications.service import (
    ParticipantNotFoundError,
    get_email_logs,
    verify_unsubscribe_token,
)
from app.domains.notifications.tasks import send_bulk_campaign, send_notification

logger = logging.getLogger(__name__)
settings = get_settings()

admin_router = APIRouter()
public_router = APIRouter()


async def _require_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de admin inválido",
        )


@admin_router.post(
    "/send",
    response_model=SendNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_require_admin_token)],
    responses={
        202: {"description": "Tarea encolada correctamente"},
        403: {"description": "Token de admin inválido"},
        404: {"description": "Participante no encontrado"},
    },
)
async def send_notification_endpoint(
    payload: SendNotificationRequest,
) -> SendNotificationResponse:
    """
    Encola un email individual para un participante.
    El envío es asíncrono via Celery — responde inmediatamente con el task_id.
    """
    task = send_notification.delay(
        str(payload.participant_id),
        payload.email_type,
        payload.context,
    )
    logger.info(
        "notification_enqueued task_id=%s participant=%s type=%s",
        task.id,
        str(payload.participant_id)[:8],
        payload.email_type,
    )
    return SendNotificationResponse(
        task_id=task.id,
        participant_id=payload.participant_id,
        email_type=payload.email_type,
        queued=True,
    )


@admin_router.post(
    "/send-bulk",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_require_admin_token)],
    responses={
        202: {"description": "Campaña masiva encolada"},
        403: {"description": "Token de admin inválido"},
    },
)
async def send_bulk_endpoint(
    payload: BulkSendRequest,
) -> dict:
    """
    Encola un envío masivo de campaña.
    Si participant_ids está vacío, envía a todos con consent_marketing=True.
    """
    participant_ids = (
        [str(pid) for pid in payload.participant_ids]
        if payload.participant_ids
        else None
    )
    task = send_bulk_campaign.delay(
        payload.email_type,
        payload.context,
        participant_ids,
    )
    logger.info(
        "bulk_campaign_enqueued task_id=%s type=%s",
        task.id,
        payload.email_type,
    )
    return {"task_id": task.id, "email_type": payload.email_type, "queued": True}


@admin_router.get(
    "/logs",
    response_model=list[EmailLogResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
)
async def get_logs_endpoint(
    participant_id: Optional[uuid.UUID] = Query(None),
    email_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[EmailLogResponse]:
    """Lista logs de envío. Filtrables por participant_id y email_type."""
    logs = await get_email_logs(db, participant_id, email_type, limit, offset)
    return [EmailLogResponse.model_validate(log) for log in logs]


@public_router.get(
    "/unsubscribe",
    status_code=status.HTTP_200_OK,
)
async def unsubscribe_endpoint(
    pid: uuid.UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Procesa la baja de marketing para un participante.
    El token HMAC previene que se den de baja participantes arbitrarios.
    """
    if not verify_unsubscribe_token(pid, token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de baja inválido o expirado",
        )

    from sqlalchemy import select

    from app.domains.participants.models import Participant

    async with db.begin():
        result = await db.execute(
            select(Participant).where(Participant.id == pid)
        )
        participant = result.scalar_one_or_none()
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante no encontrado",
            )
        participant.consent_marketing = False

    logger.info("unsubscribe participant=%s", str(pid)[:8])
    return {"unsubscribed": True, "participant_id": str(pid)}
