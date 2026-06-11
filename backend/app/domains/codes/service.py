import csv
import io
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.codes.cache import (
    get_code_status,
    invalidate_code_status,
    set_code_status,
)
from app.domains.codes.models import Code
from app.domains.codes.schemas import CodeImportResponse, CodeStatusResponse

logger = logging.getLogger(__name__)


def _mask_code(code: str) -> str:
    return f"{code[:-4]}****" if len(code) > 4 else "****"


class CodeNotFoundError(Exception):
    pass


class CodeAlreadyUsedError(Exception):
    pass


class CodeInvalidError(Exception):
    pass


async def validate_code(
    db: AsyncSession, code: str, participation_ip: str
) -> uuid.UUID:
    """
    Valida y marca el código como usado en una transacción atómica.
    SELECT FOR UPDATE serializa lecturas concurrentes sobre el mismo código,
    garantizando que exactamente un request gane la carrera.
    Devuelve el UUID del Code (participation_id para la phase-03).
    """
    masked = _mask_code(code)

    cached_status = await get_code_status(code)
    if cached_status == "used":
        logger.info("validate_code cache_hit=used code=%s ip=%s", masked, participation_ip)
        raise CodeAlreadyUsedError(code)
    if cached_status == "invalid":
        logger.info("validate_code cache_hit=invalid code=%s ip=%s", masked, participation_ip)
        raise CodeInvalidError(code)

    async with db.begin():
        result = await db.execute(
            select(Code).where(Code.code == code).with_for_update()
        )
        db_code = result.scalar_one_or_none()

        if db_code is None:
            logger.warning("validate_code not_found code=%s ip=%s", masked, participation_ip)
            raise CodeNotFoundError(code)

        if db_code.status == "used":
            logger.info("validate_code already_used code=%s ip=%s", masked, participation_ip)
            await set_code_status(code, "used")
            raise CodeAlreadyUsedError(code)

        if db_code.status == "invalid":
            logger.warning("validate_code invalid code=%s ip=%s", masked, participation_ip)
            await set_code_status(code, "invalid")
            raise CodeInvalidError(code)

        now = datetime.now(timezone.utc)
        db_code.status = "used"
        db_code.used_at = now
        db_code.activated_at = db_code.activated_at or now
        db_code.participation_ip = participation_ip

        participation_id = db_code.id

    await invalidate_code_status(code)
    logger.info("validate_code success code=%s ip=%s", masked, participation_ip)
    return participation_id


async def get_code_status_service(
    db: AsyncSession, code: str
) -> CodeStatusResponse:
    """Consulta el estado de un código sin marcarlo — siempre va a DB para timestamps."""
    masked = _mask_code(code)

    cached_status = await get_code_status(code)
    if cached_status is not None and cached_status == "unused":
        # Para 'unused' el cache es suficiente — no hay timestamps relevantes
        logger.debug("get_status cache_hit code=%s status=%s", masked, cached_status)
        return CodeStatusResponse(code=masked, status=cached_status)

    # Para 'used'/'invalid' o cache miss: siempre DB para devolver timestamps completos
    result = await db.execute(select(Code).where(Code.code == code))
    db_code = result.scalar_one_or_none()

    if db_code is None:
        raise CodeNotFoundError(code)

    if cached_status is None:
        await set_code_status(code, db_code.status)

    return CodeStatusResponse(
        code=masked,
        status=db_code.status,
        used_at=db_code.used_at,
        activated_at=db_code.activated_at,
    )


async def import_codes_from_csv(
    db: AsyncSession, csv_content: bytes
) -> CodeImportResponse:
    """
    Importación batch desde CSV. Formato esperado: una columna 'code' por fila.
    INSERT ON CONFLICT DO NOTHING garantiza idempotencia sin N+1 queries.
    """
    csv_text = csv_content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(csv_text))

    inserted = 0
    skipped = 0
    errors = 0
    batch: list[dict] = []
    BATCH_SIZE = 500

    async def flush_batch(session: AsyncSession, rows: list[dict]) -> tuple[int, int]:
        stmt = (
            pg_insert(Code)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["code"])
        )
        result = await session.execute(stmt)
        _inserted = result.rowcount
        _skipped = len(rows) - _inserted
        return _inserted, _skipped

    async with db.begin():
        for row in reader:
            raw_code = (row.get("code") or "").strip().upper()
            if not raw_code:
                errors += 1
                continue

            batch.append({"code": raw_code, "status": "unused"})

            if len(batch) >= BATCH_SIZE:
                ins, skp = await flush_batch(db, batch)
                inserted += ins
                skipped += skp
                batch.clear()

        if batch:
            ins, skp = await flush_batch(db, batch)
            inserted += ins
            skipped += skp

    logger.info(
        "import_codes inserted=%d skipped=%d errors=%d", inserted, skipped, errors
    )
    return CodeImportResponse(
        inserted=inserted,
        skipped=skipped,
        errors=errors,
        message=f"Importación completada: {inserted} insertados, {skipped} omitidos, {errors} errores",
    )
