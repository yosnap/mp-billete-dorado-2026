import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

_redis_client: aioredis.Redis | None = None

CODE_STATUS_TTL = 60  # segundos
RATE_LIMIT_WINDOW = 600  # 10 minutos en segundos
RATE_LIMIT_MAX = 5


def _key_code_status(code: str) -> str:
    return f"code:status:{code}"


def _key_rate_limit(ip: str) -> str:
    return f"rate:validate:{ip}"


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True,
        )
    return _redis_client


async def get_code_status(code: str) -> str | None:
    """Devuelve el status cacheado o None si no hay entrada."""
    client = await get_redis()
    return await client.get(_key_code_status(code))


async def set_code_status(code: str, status: str) -> None:
    client = await get_redis()
    await client.set(_key_code_status(code), status, ex=CODE_STATUS_TTL)


async def invalidate_code_status(code: str) -> None:
    """Borra la entrada tras una validación exitosa para forzar re-lectura."""
    client = await get_redis()
    await client.delete(_key_code_status(code))


async def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Incrementa el contador de intentos por IP con ventana deslizante.
    Devuelve (allowed, attempts_count).
    Usamos INCR + EXPIRE para que la ventana se reinicie tras el primer intento.
    """
    client = await get_redis()
    key = _key_rate_limit(ip)

    count = await client.incr(key)
    if count == 1:
        # Primera petición en esta ventana — establece TTL
        await client.expire(key, RATE_LIMIT_WINDOW)

    return count <= RATE_LIMIT_MAX, count
