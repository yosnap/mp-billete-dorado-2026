"""
Servicio de envío de emails para MP Billete Dorado 2026.

Flujo:
  1. Desencriptar email del participante solo en memoria (pgcrypto via SQL)
  2. Renderizar plantilla Jinja2 con el contexto del evento
  3. Enviar via SendGrid API
  4. Registrar resultado en EmailLog (sin datos personales)

El email desencriptado NUNCA se persiste ni se loguea.
"""
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from jinja2 import Environment, PackageLoader, select_autoescape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.notifications.models import EmailLog

logger = logging.getLogger(__name__)
settings = get_settings()

# Tipos de email que requieren unsubscribe link firmado (marketing)
MARKETING_EMAIL_TYPES = {
    "golden_days",
    "new_prizes_unlocked",
    "last_chance",
    "grand_final",
}

# Entorno Jinja2 apuntando al subdirectorio templates/ de este paquete
_jinja_env = Environment(
    loader=PackageLoader("app.domains.notifications", "templates"),
    autoescape=select_autoescape(["html"]),
)


class EmailSendError(Exception):
    """Error irrecuperable al enviar un email."""


class ParticipantNotFoundError(Exception):
    """El participante no existe o no tiene email registrado."""


def _build_unsubscribe_token(participant_id: uuid.UUID) -> str:
    """
    Genera un token HMAC-SHA256 no enumerable para el link de baja.
    Firmado con secret_key; no requiere estado en BD.
    """
    raw = f"unsub:{participant_id}"
    return hmac.new(
        settings.secret_key.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_unsubscribe_token(participant_id: uuid.UUID, token: str) -> bool:
    """Verifica que el token de baja es auténtico."""
    expected = _build_unsubscribe_token(participant_id)
    return hmac.compare_digest(expected, token)


async def _decrypt_participant_email(
    db: AsyncSession, participant_id: uuid.UUID
) -> Optional[str]:
    """
    Desencripta el email usando pgcrypto directamente en la consulta SQL.
    El valor plano nunca sale de esta función hacia persistencia.
    """
    result = await db.execute(
        text(
            """
            SELECT pgp_sym_decrypt(decode(email, 'base64'), :key)::text AS plain_email
            FROM participants
            WHERE id = :pid
            """
        ),
        {"key": settings.pgcrypto_key, "pid": str(participant_id)},
    )
    row = result.fetchone()
    return row.plain_email if row else None


async def _create_email_log(
    db: AsyncSession,
    participant_id: uuid.UUID,
    email_type: str,
    status: str,
    error: Optional[str] = None,
) -> EmailLog:
    """Inserta un EmailLog. No contiene datos personales del participante."""
    log = EmailLog(
        participant_id=participant_id,
        type=email_type,
        status=status,
        sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        error=error,
    )
    db.add(log)
    await db.flush()
    return log


async def _update_email_log(
    db: AsyncSession,
    log_id: uuid.UUID,
    status: str,
    error: Optional[str] = None,
) -> None:
    result = await db.execute(
        select(EmailLog).where(EmailLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if log:
        log.status = status
        log.sent_at = datetime.now(timezone.utc) if status == "sent" else log.sent_at
        log.error = error


def _render_template(
    email_type: str,
    context: dict[str, Any],
    participant_id: uuid.UUID,
) -> tuple[str, str]:
    """
    Renderiza subject + body HTML de la plantilla Jinja2.
    Inyecta unsubscribe_url para tipos de marketing.
    """
    if email_type in MARKETING_EMAIL_TYPES:
        token = _build_unsubscribe_token(participant_id)
        context = {
            **context,
            "unsubscribe_url": (
                f"{settings.allowed_origins[0]}/unsubscribe"
                f"?pid={participant_id}&token={token}"
            ),
        }

    template = _jinja_env.get_template(f"{email_type}.html")
    body_html = template.render(**context)

    # El subject se define como variable en cada plantilla o se deriva del tipo
    subjects: dict[str, str] = {
        "welcome": "Bienvenido a MP Billete Dorado 2026",
        "winner": "¡Enhorabuena! Has ganado un premio",
        "no_prize": "Gracias por participar en MP Billete Dorado",
        "golden_days": "Los Días Dorados MP han llegado",
        "new_prizes_unlocked": "Se han desbloqueado nuevos premios",
        "last_chance": "Última oportunidad — MP Billete Dorado cierra pronto",
        "grand_final": "Gran Final MP Billete Dorado 2026",
        "instant_winner_sms": "¡Has ganado en MP Billete Dorado!",
        "instant_no_prize_sms": "Gracias por participar en MP Billete Dorado",
    }
    return subjects.get(email_type, "Notificación MP Billete Dorado"), body_html


def _send_via_sendgrid(
    to_email: str,
    subject: str,
    body_html: str,
    from_email: str = "noreply@mainpaper.com",
) -> None:
    """
    Envía el email usando la API de SendGrid.
    Lanza EmailSendError si la API devuelve un error.
    """
    api_key = getattr(settings, "sendgrid_api_key", None)
    if not api_key:
        raise EmailSendError("SENDGRID_API_KEY no configurada")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body_html,
    )
    client = SendGridAPIClient(api_key)
    response = client.send(message)

    if response.status_code not in (200, 201, 202):
        raise EmailSendError(
            f"SendGrid error status={response.status_code} body={response.body}"
        )


async def send_email(
    db: AsyncSession,
    participant_id: uuid.UUID,
    email_type: str,
    context: dict[str, Any],
) -> EmailLog:
    """
    Punto de entrada principal para enviar un email.

    Desencripta el email solo en memoria, renderiza la plantilla,
    envía via SendGrid y registra el resultado en EmailLog.
    """
    # Crear log con estado pending antes del envío
    async with db.begin():
        log = await _create_email_log(db, participant_id, email_type, "pending")
        log_id = log.id

    plain_email: Optional[str] = None
    try:
        # Desencriptar email — solo en memoria
        plain_email = await _decrypt_participant_email(db, participant_id)
        if not plain_email:
            raise ParticipantNotFoundError(participant_id)

        subject, body_html = _render_template(email_type, context, participant_id)
        _send_via_sendgrid(plain_email, subject, body_html)

        async with db.begin():
            await _update_email_log(db, log_id, "sent")

        logger.info(
            "email_sent participant=%s type=%s",
            str(participant_id)[:8],
            email_type,
        )

    except Exception as exc:
        error_msg = type(exc).__name__ + ": " + str(exc)
        async with db.begin():
            await _update_email_log(db, log_id, "failed", error=error_msg[:500])

        logger.error(
            "email_failed participant=%s type=%s error=%s",
            str(participant_id)[:8],
            email_type,
            error_msg[:200],
        )
        raise

    finally:
        # Asegurar que el email plano no permanece en scope
        del plain_email

    result = await db.execute(select(EmailLog).where(EmailLog.id == log_id))
    return result.scalar_one()


async def get_email_logs(
    db: AsyncSession,
    participant_id: Optional[uuid.UUID] = None,
    email_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[EmailLog]:
    """Consulta logs de envío para el panel admin."""
    query = select(EmailLog).order_by(EmailLog.created_at.desc())

    if participant_id:
        query = query.where(EmailLog.participant_id == participant_id)
    if email_type:
        query = query.where(EmailLog.type == email_type)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
