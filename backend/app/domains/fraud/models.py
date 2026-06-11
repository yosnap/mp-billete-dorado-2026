import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FraudEvent(Base):
    __tablename__ = "fraud_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    # Valores: 'ip_abuse' | 'bot_ua' | 'fast_submission'
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Contexto extra: count, ua, ip, etc.
    detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_fraud_events_ip_created", "ip_address", "created_at"),
        Index("ix_fraud_events_event_type", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<FraudEvent type={self.event_type} ip={self.ip_address}>"
