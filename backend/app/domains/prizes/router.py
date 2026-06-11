import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.codes.cache import check_rate_limit
from app.domains.prizes.schemas import PrizeResponse, PrizeToggleResponse, SpinRequest, SpinResponse
from app.domains.prizes.service import (
    InvalidParticipationError,
    NoAvailablePrizesError,
    ParticipationAlreadySpunError,
    PrizeNotFoundError,
    get_catalog_public,
    spin,
    toggle_prize,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
admin_router = APIRouter()


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def _require_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de admin inválido",
        )


@router.post(
    "/spin",
    response_model=SpinResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Participación inválida o no encontrada"},
        409: {"description": "Esta participación ya realizó su ruleta"},
        429: {"description": "Demasiados intentos"},
    },
)
async def spin_endpoint(
    payload: SpinRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SpinResponse:
    ip = _get_client_ip(request)

    allowed, attempts = await check_rate_limit(ip)
    if not allowed:
        logger.warning("spin rate_limit_exceeded ip=%s attempts=%d", ip, attempts)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta de nuevo en 10 minutos.",
            headers={"Retry-After": "600"},
        )

    try:
        return await spin(db, payload.participation_id)
    except InvalidParticipationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participación inválida o no encontrada",
        )
    except ParticipationAlreadySpunError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta participación ya realizó su ruleta",
        )
    except NoAvailablePrizesError:
        return SpinResponse(won=False, prize=None)


@router.get(
    "/catalog",
    response_model=list[PrizeResponse],
    status_code=status.HTTP_200_OK,
)
async def catalog_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[PrizeResponse]:
    """Catálogo público de premios disponibles. No expone stock exacto."""
    return await get_catalog_public(db)


@admin_router.put(
    "/prizes/{prize_id}/toggle",
    response_model=PrizeToggleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
    responses={
        403: {"description": "Token de admin inválido"},
        404: {"description": "Premio no encontrado"},
    },
)
async def toggle_prize_endpoint(
    prize_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PrizeToggleResponse:
    try:
        prize = await toggle_prize(db, prize_id)
    except PrizeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premio no encontrado",
        )
    return PrizeToggleResponse(id=prize.id, is_active=prize.is_active)
