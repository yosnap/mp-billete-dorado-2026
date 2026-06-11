import json

from app.domains.codes.cache import get_redis

PRIZES_CATALOG_TTL = 30   # segundos — baja para reflejar cambios de stock pronto
PARTICIPATION_COUNT_TTL = 10  # segundos — ventana corta para precisión de fase


def _key_prizes_catalog(phase: int) -> str:
    return f"prizes:catalog:phase:{phase}"


def _key_participation_count() -> str:
    return "prizes:participation_count"


async def get_prizes_catalog(phase: int) -> list | None:
    """Devuelve el catálogo de premios disponibles para la fase dada, o None si hay cache miss."""
    client = await get_redis()
    raw = await client.get(_key_prizes_catalog(phase))
    if raw is None:
        return None
    return json.loads(raw)


async def set_prizes_catalog(phase: int, prizes: list) -> None:
    """Guarda el catálogo serializado en caché con TTL de 30s."""
    client = await get_redis()
    await client.set(_key_prizes_catalog(phase), json.dumps(prizes), ex=PRIZES_CATALOG_TTL)


async def invalidate_prizes_catalog() -> None:
    """Borra todas las claves de catálogo (fases 1-4) tras cambios de stock o toggle."""
    client = await get_redis()
    keys = [_key_prizes_catalog(phase) for phase in range(1, 5)]
    await client.delete(*keys)


async def get_participation_count() -> int | None:
    """Devuelve el conteo cacheado de participaciones o None si hay cache miss."""
    client = await get_redis()
    raw = await client.get(_key_participation_count())
    if raw is None:
        return None
    return int(raw)


async def set_participation_count(count: int) -> None:
    """Guarda el conteo total de participaciones con TTL de 10s."""
    client = await get_redis()
    await client.set(_key_participation_count(), count, ex=PARTICIPATION_COUNT_TTL)
