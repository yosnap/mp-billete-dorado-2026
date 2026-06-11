import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.codes.cache import get_redis
from app.domains.fraud.models import FraudEvent

logger = logging.getLogger(__name__)

# Umbral: más de 3 participaciones desde la misma IP en 24h → abuso
IP_ABUSE_THRESHOLD = 3
IP_ABUSE_WINDOW_HOURS = 24

# Patrones de user-agent que indican automatización
BOT_PATTERNS = [
    "bot", "crawler", "spider", "headless",
    "puppeteer", "playwright", "selenium",
]

# Ventana de fast-submission: misma IP más de 1 request en 5 segundos
FAST_SUBMISSION_TTL = 5  # segundos
_FAST_KEY_PREFIX = "fraud:fast:"


async def check(
    db: AsyncSession,
    ip: str,
    user_agent: Optional[str],
) -> list[FraudEvent]:
    """
    Evalúa las tres reglas antifraude y crea los FraudEvent correspondientes.
    Nunca lanza excepción — los errores se loguean y se ignoran para no
    bloquear el flujo de registro del participante.
    Los eventos deben insertarse dentro de la transacción activa del llamador.
    """
    events: list[FraudEvent] = []

    try:
        events.extend(await _check_ip_abuse(db, ip))
    except Exception as exc:
        logger.warning("fraud_check ip_abuse_error ip=%s error=%s", ip, exc)

    try:
        events.extend(_check_bot_ua(ip, user_agent))
    except Exception as exc:
        logger.warning("fraud_check bot_ua_error ip=%s error=%s", ip, exc)

    try:
        events.extend(await _check_fast_submission(ip))
    except Exception as exc:
        logger.warning("fraud_check fast_submission_error ip=%s error=%s", ip, exc)

    for event in events:
        db.add(event)
        logger.info(
            "fraud_event type=%s ip=%s detail=%s",
            event.event_type, ip, event.detail,
        )

    return events


async def _check_ip_abuse(db: AsyncSession, ip: str) -> list[FraudEvent]:
    """Regla 1: detecta abuso de IP con más de 3 registros en las últimas 24h."""
    window_start = datetime.now(timezone.utc) - timedelta(hours=IP_ABUSE_WINDOW_HOURS)

    # Importación local para evitar ciclo participants → fraud → participants
    from app.domains.participants.models import Participant  # noqa: PLC0415

    result = await db.execute(
        select(func.count()).where(
            Participant.ip_address == ip,
            Participant.created_at >= window_start,
        )
    )
    count = result.scalar_one()

    if count >= IP_ABUSE_THRESHOLD:
        return [
            FraudEvent(
                ip_address=ip,
                event_type="ip_abuse",
                detail={"count": count, "ip": ip},
            )
        ]
    return []


def _check_bot_ua(ip: str, user_agent: Optional[str]) -> list[FraudEvent]:
    """Regla 2: detecta user-agents asociados a herramientas de automatización."""
    if not user_agent:
        return []

    ua_lower = user_agent.lower()
    matched = next((p for p in BOT_PATTERNS if p in ua_lower), None)

    if matched:
        return [
            FraudEvent(
                ip_address=ip,
                event_type="bot_ua",
                detail={"ua": user_agent[:200]},
            )
        ]
    return []


async def _check_fast_submission(ip: str) -> list[FraudEvent]:
    """
    Regla 3: detecta envíos consecutivos muy rápidos desde la misma IP.
    Usa Redis con TTL de 5s — si la clave ya existe, la IP ha enviado
    más de una solicitud en esa ventana.
    """
    client = await get_redis()
    key = f"{_FAST_KEY_PREFIX}{ip}"

    # SET NX: sólo escribe si no existe — devuelve True si fue creada
    was_set = await client.set(key, "1", ex=FAST_SUBMISSION_TTL, nx=True)

    if not was_set:
        # La clave ya existía → envío demasiado rápido
        return [
            FraudEvent(
                ip_address=ip,
                event_type="fast_submission",
                detail={"ip": ip},
            )
        ]

    return []
