import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CodeValidateRequest(BaseModel):
    code: str = Field(..., min_length=15, max_length=20, description="Código MP-XXXX-XXXX-XXXX")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class CodeValidateResponse(BaseModel):
    valid: bool
    participation_id: uuid.UUID
    message: str = "Código validado correctamente"


class CodeStatusResponse(BaseModel):
    code: str
    status: str
    used_at: datetime | None = None
    activated_at: datetime | None = None


class CodeImportRequest(BaseModel):
    """Metadatos opcionales para la importación batch."""
    overwrite_invalid: bool = False


class CodeImportResponse(BaseModel):
    inserted: int
    skipped: int
    errors: int
    message: str


class ErrorResponse(BaseModel):
    detail: str
