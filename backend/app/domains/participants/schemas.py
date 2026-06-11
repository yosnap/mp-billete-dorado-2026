import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class ParticipantRegisterRequest(BaseModel):
    code: str = Field(..., description="Código del billete previamente validado")
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    # consent_legal debe ser True; se valida en el service para error de dominio claro
    consent_legal: bool
    consent_marketing: bool = False

    @model_validator(mode="after")
    def normalize_code(self) -> "ParticipantRegisterRequest":
        self.code = self.code.strip().upper()
        return self


class ParticipantRegisterResponse(BaseModel):
    participant_id: uuid.UUID
    # participation_id es el code_id (codes.id) — usado por el frontend para polling
    participation_id: uuid.UUID
