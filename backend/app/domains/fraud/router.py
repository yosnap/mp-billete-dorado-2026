import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.codes.models import Code
from app.domains.fraud.models import FraudEvent

logger = logging.getLogger(__name__)
settings = get_settings()

admin_fraud_router = APIRouter()


async def _require_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de admin inválido",
        )


class FraudEventResponse(BaseModel):
    id: uuid.UUID
    ip_address: str
    event_type: str
    detail: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FraudEventListResponse(BaseModel):
    items: list[FraudEventResponse]
    total_count: int
    page: int
    page_size: int


class CodeInvalidateResponse(BaseModel):
    code_id: uuid.UUID
    invalidated: bool


@admin_fraud_router.get(
    "/flags",
    response_model=FraudEventListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
)
async def list_fraud_flags(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> FraudEventListResponse:
    base_query = select(FraudEvent)
    count_query = select(func.count()).select_from(FraudEvent)

    if event_type:
        base_query = base_query.where(FraudEvent.event_type == event_type)
        count_query = count_query.where(FraudEvent.event_type == event_type)

    total_result = await db.execute(count_query)
    total_count = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base_query.order_by(FraudEvent.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(items_result.scalars().all())

    return FraudEventListResponse(
        items=[FraudEventResponse.model_validate(e) for e in items],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@admin_fraud_router.post(
    "/invalidate/{code_id}",
    response_model=CodeInvalidateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
)
async def invalidate_code(
    code_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CodeInvalidateResponse:
    async with db.begin():
        result = await db.execute(
            select(Code).where(Code.id == code_id)
        )
        db_code = result.scalar_one_or_none()

        if db_code is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código no encontrado",
            )

        db_code.status = "invalid"

    logger.info("admin invalidate_code code_id=%s", code_id)
    return CodeInvalidateResponse(code_id=code_id, invalidated=True)
