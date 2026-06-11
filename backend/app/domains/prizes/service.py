import logging
import random
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.codes.models import Code
from app.domains.notifications.tasks import send_notification
from app.domains.prizes.cache import (
    get_participation_count,
    get_prizes_catalog,
    invalidate_prizes_catalog,
    set_participation_count,
    set_prizes_catalog,
)
from app.domains.prizes.models import Prize, PrizeAssignment
from app.domains.prizes.phase_manager import get_current_phase
from app.domains.prizes.schemas import PrizeResponse, SpinResponse

logger = logging.getLogger(__name__)

# Probabilidad base de ganar: 4835 premios sobre 35000 participaciones esperadas
WIN_PROBABILITY = 4835 / 35_000


class PrizeNotFoundError(Exception):
    pass


class InvalidParticipationError(Exception):
    pass


class ParticipationAlreadySpunError(Exception):
    pass


class NoAvailablePrizesError(Exception):
    pass


async def get_participation_count_service(db: AsyncSession) -> int:
    """
    Devuelve el conteo de participaciones con status='used'.
    Usa caché con TTL de 10s para evitar COUNT(*) en cada spin.
    """
    cached = await get_participation_count()
    if cached is not None:
        return cached

    result = await db.execute(
        select(func.count()).select_from(Code).where(Code.status == "used")
    )
    count = result.scalar_one()
    await set_participation_count(count)
    logger.debug("participation_count db_hit count=%d", count)
    return count


async def get_available_prizes(db: AsyncSession, current_phase: int) -> list[Prize]:
    """
    Devuelve premios activos con stock disponible desbloqueados hasta la fase actual.
    Usa caché por fase con TTL de 30s.
    """
    cached = await get_prizes_catalog(current_phase)
    if cached is not None:
        # Reconstruir objetos Prize desde la representación cacheada
        prizes = []
        for item in cached:
            p = Prize()
            p.id = uuid.UUID(item["id"])
            p.name = item["name"]
            p.description = item.get("description")
            p.category = item["category"]
            p.total_quantity = item["total_quantity"]
            p.remaining_quantity = item["remaining_quantity"]
            p.is_active = item["is_active"]
            p.unlock_at = item.get("unlock_at")
            prizes.append(p)
        return prizes

    result = await db.execute(
        select(Prize).where(
            Prize.is_active.is_(True),
            Prize.remaining_quantity > 0,
            (Prize.unlock_at.is_(None)) | (Prize.unlock_at <= current_phase),
        )
    )
    prizes = list(result.scalars().all())

    serialized = [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "total_quantity": p.total_quantity,
            "remaining_quantity": p.remaining_quantity,
            "is_active": p.is_active,
            "unlock_at": p.unlock_at,
        }
        for p in prizes
    ]
    await set_prizes_catalog(current_phase, serialized)
    logger.debug("prizes_catalog db_hit phase=%d count=%d", current_phase, len(prizes))
    return prizes


async def spin(db: AsyncSession, participation_id: uuid.UUID) -> SpinResponse:
    """
    Motor de ruleta: determina si la participación gana un premio.

    Todo el flujo corre dentro de una única transacción para evitar el error
    InvalidRequestError que se produce al anidar db.begin() sobre una sesión
    con autobegin ya activo.

    Garantías de consistencia:
    - pg_advisory_xact_lock serializa spins concurrentes sobre el mismo prize_id
    - SELECT FOR UPDATE en el premio elegido previene overselling
    - UNIQUE constraint en prize_assignments impide doble premio por participación
    - IntegrityError capturado como fallback ante race condition en la verificación previa
    """
    masked_pid = str(participation_id)[:8] + "..."

    # Lecturas de caché fuera de transacción (solo Redis, sin DB)
    count = await get_participation_count_service(db)
    phase = get_current_phase(count)
    available = await get_available_prizes(db, phase)

    # Decisión probabilística antes de abrir la transacción.
    # audit_roll se guarda en PrizeAssignment para reproducir el resultado en auditorías.
    audit_roll = random.random()
    if not available or audit_roll >= WIN_PROBABILITY:
        logger.info(
            "spin result=no_win participation=%s phase=%d available=%d roll=%.6f",
            masked_pid, phase, len(available), audit_roll,
        )
        # Trigger asíncrono: encolar email de no-ganador
        try:
            send_notification.delay(str(participation_id), "no_prize", {})
        except Exception as notify_exc:
            logger.error(
                "spin notify_no_prize_enqueue_failed participation=%s error=%s",
                masked_pid, str(notify_exc)[:100],
            )
        return SpinResponse(won=False, prize=None)

    weights = [p.remaining_quantity for p in available]
    selected = random.choices(available, weights=weights, k=1)[0]

    # Único bloque de transacción que incluye todas las lecturas y escrituras DB
    async with db.begin():
        # 1. Verificar participación válida dentro de la transacción
        code_result = await db.execute(
            select(Code).where(Code.id == participation_id, Code.status == "used")
        )
        if code_result.scalar_one_or_none() is None:
            logger.warning("spin invalid_participation participation=%s", masked_pid)
            raise InvalidParticipationError(participation_id)

        # 2. Verificar ausencia de asignación previa
        existing = await db.execute(
            select(PrizeAssignment).where(
                PrizeAssignment.participation_id == participation_id
            )
        )
        if existing.scalar_one_or_none() is not None:
            logger.info("spin already_spun participation=%s", masked_pid)
            raise ParticipationAlreadySpunError(participation_id)

        # 3. Advisory lock por prize_id — serializa asignaciones del mismo premio
        lock_key = selected.id.int & 0x7FFFFFFFFFFFFFFF
        await db.execute(text(f"SELECT pg_advisory_xact_lock({lock_key})"))

        # 4. Re-verificar stock con SELECT FOR UPDATE dentro de la transacción
        prize_result = await db.execute(
            select(Prize)
            .where(Prize.id == selected.id, Prize.remaining_quantity > 0)
            .with_for_update()
        )
        locked_prize = prize_result.scalar_one_or_none()

        if locked_prize is None:
            # Race condition: el premio se agotó entre la selección y el lock
            logger.warning(
                "spin race_condition prize=%s participation=%s",
                str(selected.id)[:8], masked_pid,
            )
            return SpinResponse(won=False, prize=None)

        try:
            assignment = PrizeAssignment(
                participation_id=participation_id,
                prize_id=locked_prize.id,
                audit_seed=audit_roll,
            )
            db.add(assignment)
            locked_prize.remaining_quantity -= 1
            await db.flush()
        except IntegrityError:
            # Fallback: race condition entre verificación previa y el INSERT
            logger.info(
                "spin integrity_error_double_spin participation=%s", masked_pid
            )
            raise ParticipationAlreadySpunError(participation_id)

    # Invalidar caché tras commit exitoso
    await invalidate_prizes_catalog()

    prize_response = PrizeResponse(
        id=locked_prize.id,
        name=locked_prize.name,
        description=locked_prize.description,
        available=locked_prize.remaining_quantity > 0,
    )

    # Trigger asíncrono: encolar email de ganador para el participante
    # El participante se obtiene por code_id=participation_id
    try:
        send_notification.delay(
            str(participation_id),
            "winner",
            {
                "prize_name": locked_prize.name,
                "prize_description": locked_prize.description,
                "code": str(participation_id),
            },
        )
    except Exception as notify_exc:
        # El fallo de la notificación no debe revertir el spin ya confirmado
        logger.error(
            "spin notify_enqueue_failed participation=%s error=%s",
            masked_pid,
            str(notify_exc)[:100],
        )

    logger.info(
        "spin result=win participation=%s prize=%s phase=%d remaining=%d",
        masked_pid, str(locked_prize.id)[:8], phase, locked_prize.remaining_quantity,
    )
    return SpinResponse(won=True, prize=prize_response)


async def get_catalog_public(db: AsyncSession) -> list[PrizeResponse]:
    """
    Devuelve catálogo público de premios activos.
    No expone stock exacto — solo available: bool.
    """
    count = await get_participation_count_service(db)
    phase = get_current_phase(count)
    prizes = await get_available_prizes(db, phase)

    return [
        PrizeResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            available=p.remaining_quantity > 0,
        )
        for p in prizes
    ]


async def toggle_prize(db: AsyncSession, prize_id: uuid.UUID) -> Prize:
    """Activa/desactiva un premio e invalida la caché del catálogo."""
    async with db.begin():
        result = await db.execute(
            select(Prize).where(Prize.id == prize_id).with_for_update()
        )
        prize = result.scalar_one_or_none()
        if prize is None:
            raise PrizeNotFoundError(prize_id)

        prize.is_active = not prize.is_active

    await invalidate_prizes_catalog()
    logger.info("toggle_prize prize=%s is_active=%s", str(prize_id)[:8], prize.is_active)
    return prize
