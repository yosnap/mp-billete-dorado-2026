import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # Email almacenado como bytes hex de pgcrypto — el service encripta/desencripta
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # Relación 1:1 con el código validado — UNIQUE garantizado por migración
    code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("codes.id", name="fk_participants_code"),
        nullable=False,
        unique=True,
    )
    prize_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prizes.id", name="fk_participants_prize"),
        nullable=True,
    )
    # Consentimientos RGPD — consent_legal debe ser True para registrar
    consent_legal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    consent_marketing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # Metadatos de sesión para antifraude y auditoría
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<Participant id={self.id} code_id={self.code_id}>"
