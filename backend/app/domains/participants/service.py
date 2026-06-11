import logging
import uuid
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.codes.models import Code
from app.domains.fraud import detector as fraud_detector
from app.domains.participants.models import Participant
from app.domains.participants.schemas import (
    ParticipantRegisterRequest,
    ParticipantRegisterResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ConsentRequiredError(Exception):
    """El participante no aceptó el consentimiento legal obligatorio."""


class CodeNotValidatedError(Exception):
    """El código no está en status='used' — debe validarse primero."""


class CodeAlreadyRegisteredError(Exception):
    """Ya existe un participante registrado con ese código."""


async def register(
    db: AsyncSession,
    payload: ParticipantRegisterRequest,
    ip: str,
    user_agent: Optional[str],
) -> ParticipantRegisterResponse:
    """
    Registra un participante vinculado a un código ya validado.
    El email se encripta con pgcrypto (pgp_sym_encrypt) antes de persistir.
    Las comprobaciones de fraude se realizan dentro de la misma transacción
    pero nunca bloquean el registro — sólo lo registran.
    """
    if not payload.consent_legal:
        raise ConsentRequiredError("consent_legal es obligatorio")

    async with db.begin():
        # 1. Verificar que el código existe y ya fue marcado como 'used'
        code_result = await db.execute(
            select(Code).where(Code.code == payload.code)
        )
        db_code = code_result.scalar_one_or_none()

        if db_code is None or db_code.status != "used":
            logger.warning(
                "register code_not_validated code=%s ip=%s",
                _mask_code(payload.code), ip,
            )
            raise CodeNotValidatedError(payload.code)

        code_id: uuid.UUID = db_code.id

        # 2. Verificar que el código no tiene ya un participante (doble registro)
        existing = await db.execute(
            select(Participant).where(Participant.code_id == code_id)
        )
        if existing.scalar_one_or_none() is not None:
            logger.warning(
                "register code_already_registered code_id=%s ip=%s", code_id, ip
            )
            raise CodeAlreadyRegisteredError(str(code_id))

        # 3. Detección de fraude — no bloquea, sólo registra eventos
        await fraud_detector.check(db, ip, user_agent)

        # 4. Encriptar email con pgcrypto via SQL raw
        encrypted_email_result = await db.execute(
            text("SELECT pgp_sym_encrypt(:email, :key)"),
            {"email": payload.email, "key": settings.pgcrypto_key},
        )
        encrypted_email: str = encrypted_email_result.scalar_one()

        # 5. Insertar participante
        participant = Participant(
            email=encrypted_email,
            full_name=payload.full_name,
            phone=payload.phone,
            code_id=code_id,
            consent_legal=payload.consent_legal,
            consent_marketing=payload.consent_marketing,
            ip_address=ip,
            user_agent=user_agent,
        )
        db.add(participant)
        await db.flush()  # obtiene el id generado antes del commit

        participant_id = participant.id

    logger.info(
        "register success participant_id=%s code_id=%s ip=%s",
        participant_id, code_id, ip,
    )

    return ParticipantRegisterResponse(
        participant_id=participant_id,
        participation_id=code_id,
    )


async def get_participant_by_code(
    db: AsyncSession,
    code_id: uuid.UUID,
) -> Optional[Participant]:
    """
    Recupera el participante asociado a un code_id.
    El email devuelto está desencriptado para uso interno (notificaciones).
    """
    result = await db.execute(
        select(Participant).where(Participant.code_id == code_id)
    )
    participant = result.scalar_one_or_none()

    if participant is None:
        return None

    # Desencriptar email en memoria para uso interno
    decrypted_result = await db.execute(
        text("SELECT pgp_sym_decrypt(:data::bytea, :key)"),
        {"data": participant.email, "key": settings.pgcrypto_key},
    )
    participant.email = decrypted_result.scalar_one()

    return participant


def _mask_code(code: str) -> str:
    return f"{code[:-4]}****" if len(code) > 4 else "****"
