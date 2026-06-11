import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Tipos de email válidos en la campaña MP Billete Dorado 2026
EMAIL_TYPES = (
    "welcome",
    "winner",
    "no_prize",
    "golden_days",
    "new_prizes_unlocked",
    "last_chance",
    "grand_final",
    "instant_winner_sms",
    "instant_no_prize_sms",
)

# Estados posibles del envío
EMAIL_STATUSES = ("pending", "sent", "failed")


class EmailLog(Base):
    """
    Registro de cada intento de envío de email.
    Nunca persiste el email en claro — solo participant_id y tipo.
    """

    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", name="fk_email_logs_participant", ondelete="CASCADE"),
        nullable=False,
    )
    # Uno de los 9 tipos definidos en EMAIL_TYPES
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # pending → sent | failed tras el intento del worker
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Mensaje de error en texto plano — sin datos personales
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<EmailLog participant={self.participant_id} type={self.type} status={self.status}>"
