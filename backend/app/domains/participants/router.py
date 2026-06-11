import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.codes.cache import check_rate_limit
from app.domains.participants.schemas import (
    ParticipantRegisterRequest,
    ParticipantRegisterResponse,
)
from app.domains.participants.service import (
    CodeAlreadyRegisteredError,
    CodeNotValidatedError,
    ConsentRequiredError,
    register,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("User-Agent")


@router.post(
    "/register",
    response_model=ParticipantRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Código no validado previamente"},
        409: {"description": "Código ya registrado por otro participante"},
        422: {"description": "Consentimiento legal requerido o datos inválidos"},
        429: {"description": "Demasiados intentos desde esta IP"},
    },
)
async def register_participant(
    payload: ParticipantRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ParticipantRegisterResponse:
    ip = _get_client_ip(request)

    allowed, attempts = await check_rate_limit(ip)
    if not allowed:
        logger.warning("register rate_limit_exceeded ip=%s attempts=%d", ip, attempts)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de registro. Intenta de nuevo en 10 minutos.",
            headers={"Retry-After": "600"},
        )

    try:
        return await register(db, payload, ip, _get_user_agent(request))
    except ConsentRequiredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes aceptar los términos legales para participar.",
        )
    except CodeNotValidatedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código no ha sido validado. Valida tu código antes de registrarte.",
        )
    except CodeAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este código ya fue utilizado para registrar un participante.",
        )
