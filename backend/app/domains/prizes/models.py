import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Categoría del premio — confidencial, nunca se expone en API pública
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    # Umbral de fase en el que se desbloquea (0=siempre, 25, 50, 75)
    unlock_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_prizes_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Prize {self.name!r} remaining={self.remaining_quantity}>"


class PrizeAssignment(Base):
    __tablename__ = "prize_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # FK a codes.id — el UUID de la participación que ganó el premio
    participation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("codes.id", ondelete="CASCADE"),
        nullable=False,
    )
    prize_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prizes.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    # Valor float del random usado en el spin — permite reproducir el resultado en auditorías
    audit_seed: Mapped[float | None] = mapped_column(
        Numeric(precision=20, scale=18), nullable=True
    )

    __table_args__ = (
        # Una participación puede ganar como máximo un premio
        UniqueConstraint("participation_id", name="uq_prize_assignments_participation"),
        Index("ix_prize_assignments_prize_id", "prize_id"),
    )

    def __repr__(self) -> str:
        return f"<PrizeAssignment participation={self.participation_id} prize={self.prize_id}>"
