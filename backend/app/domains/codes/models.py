import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Code(Base):
    __tablename__ = "codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="unused"
    )
    # Momento en que el código fue activado para la campaña (puede diferir de created_at)
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # IP del participante — requerida por bases legales RGPD
    participation_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_codes_code", "code"),
        Index("ix_codes_status", "status"),
    )

    def __repr__(self) -> str:
        masked = f"{self.code[:-4]}****" if self.code else "?"
        return f"<Code {masked} status={self.status}>"
