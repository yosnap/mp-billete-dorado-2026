import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.codes.cache import check_rate_limit
from app.domains.codes.schemas import (
    CodeImportResponse,
    CodeStatusResponse,
    CodeValidateRequest,
    CodeValidateResponse,
)
from app.domains.codes.service import (
    CodeAlreadyUsedError,
    CodeInvalidError,
    CodeNotFoundError,
    get_code_status_service,
    import_codes_from_csv,
    validate_code,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
admin_router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """
    Usa request.client.host (IP de la conexión TCP directa).
    Nginx corre en la misma red Docker interna — el host es siempre el proxy confiable.
    X-Forwarded-For no se usa aquí porque puede ser falsificado por el cliente final.
    """
    return request.client.host if request.client else "unknown"


async def _require_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token de admin inválido")


@router.post(
    "/validate",
    response_model=CodeValidateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Código no encontrado"},
        409: {"description": "Código ya utilizado o inválido"},
        429: {"description": "Demasiados intentos"},
    },
)
async def validate_code_endpoint(
    payload: CodeValidateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CodeValidateResponse:
    ip = _get_client_ip(request)

    allowed, attempts = await check_rate_limit(ip)
    if not allowed:
        logger.warning("rate_limit_exceeded ip=%s attempts=%d", ip, attempts)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de validación. Intenta de nuevo en 10 minutos.",
            headers={"Retry-After": "600"},
        )

    try:
        participation_id = await validate_code(db, payload.code, ip)
    except CodeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código no encontrado")
    except CodeAlreadyUsedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código ya fue utilizado")
    except CodeInvalidError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código inválido")

    return CodeValidateResponse(valid=True, participation_id=participation_id)


@router.get(
    "/{code}/status",
    response_model=CodeStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Código no encontrado"},
        429: {"description": "Demasiados intentos"},
    },
)
async def get_code_status_endpoint(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CodeStatusResponse:
    ip = _get_client_ip(request)

    allowed, attempts = await check_rate_limit(ip)
    if not allowed:
        logger.warning("rate_limit_exceeded_status ip=%s attempts=%d", ip, attempts)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta de nuevo en 10 minutos.",
            headers={"Retry-After": "600"},
        )

    try:
        return await get_code_status_service(db, code.strip().upper())
    except CodeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código no encontrado")


@admin_router.post(
    "/codes/import",
    response_model=CodeImportResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_admin_token)],
)
async def import_codes_endpoint(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> CodeImportResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un archivo CSV",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el límite de 10 MB",
        )

    return await import_codes_from_csv(db, content)
