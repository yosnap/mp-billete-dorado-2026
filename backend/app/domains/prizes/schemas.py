import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PrizeResponse(BaseModel):
    """Schema público — sin stock exacto ni información de fases."""

    id: uuid.UUID
    name: str
    description: str | None = None
    # available=True si remaining_quantity > 0 e is_active=True
    available: bool

    model_config = {"from_attributes": True}


class PrizeAdminResponse(BaseModel):
    """Schema de administración — incluye stock completo y metadatos internos."""

    id: uuid.UUID
    name: str
    description: str | None = None
    category: str
    total_quantity: int
    remaining_quantity: int
    is_active: bool
    unlock_at: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SpinRequest(BaseModel):
    participation_id: uuid.UUID = Field(
        ..., description="UUID de la participación (codes.id) con status='used'"
    )


class SpinResponse(BaseModel):
    won: bool
    prize: PrizeResponse | None = None


class PrizeToggleResponse(BaseModel):
    id: uuid.UUID
    is_active: bool
