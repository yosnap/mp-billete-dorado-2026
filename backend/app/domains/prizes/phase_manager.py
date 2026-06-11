# Estrategia de desbloqueo por fases — CONFIDENCIAL, nunca exponer en API pública.
# Los umbrales representan el % de participaciones totales necesario para desbloquear cada fase.

TOTAL_PARTICIPATIONS = 35_000

# Umbral mínimo de % para activar cada fase
PHASE_THRESHOLDS = {1: 0, 2: 25, 3: 50, 4: 75}


def get_current_phase(participation_count: int) -> int:
    """
    Devuelve la fase actual (1-4) según el porcentaje de participaciones completadas
    respecto al total esperado de la campaña.
    """
    pct = (participation_count / TOTAL_PARTICIPATIONS) * 100
    if pct >= 75:
        return 4
    if pct >= 50:
        return 3
    if pct >= 25:
        return 2
    return 1


def get_unlocked_phases(current_phase: int) -> list[int]:
    """Devuelve la lista de fases desbloqueadas (todas las <= fase actual)."""
    return list(range(1, current_phase + 1))
