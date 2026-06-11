import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator

from app.domains.notifications.models import EMAIL_TYPES

EmailType = Literal[
    "welcome",
    "winner",
    "no_prize",
    "golden_days",
    "new_prizes_unlocked",
    "last_chance",
    "grand_final",
    "instant_winner_sms",
    "instant_no_prize_sms",
]


class SendNotificationRequest(BaseModel):
    """Body del endpoint admin POST /notifications/send."""

    participant_id: uuid.UUID
    email_type: EmailType
    # Contexto extra para la plantilla (nombre del premio, fecha, etc.)
    context: dict[str, Any] = {}


class BulkSendRequest(BaseModel):
    """Envío masivo de un tipo de email a todos los participantes con consentimiento."""

    email_type: EmailType
    context: dict[str, Any] = {}
    # Si se provee, solo se envía a los participant_ids listados
    participant_ids: Optional[list[uuid.UUID]] = None

    @field_validator("email_type")
    @classmethod
    def validate_email_type(cls, v: str) -> str:
        if v not in EMAIL_TYPES:
            raise ValueError(f"Tipo de email inválido: {v}")
        return v


class EmailLogResponse(BaseModel):
    """Representación pública de un EmailLog para la API admin."""

    id: uuid.UUID
    participant_id: uuid.UUID
    type: str
    status: str
    sent_at: Optional[datetime]
    error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SendNotificationResponse(BaseModel):
    """Respuesta tras encolar una tarea de notificación."""

    task_id: str
    participant_id: uuid.UUID
    email_type: str
    queued: bool
