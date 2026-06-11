"""
Script de seed: carga los 4.835 premios iniciales de la campaña MP Billete Dorado 2026.

Distribución:
  - small   (fase 1): 3.000 premios × 1 stock c/u  = 3.000 unidades
  - medium  (fase 2):   900 premios × 1 stock c/u  =   900 unidades
  - medium  (fase 3):   600 premios × 1 stock c/u  =   600 unidades
  - special (fase 3):   200 premios × 1 stock c/u  =   200 unidades  (iPad, becas, etc.)
  - special (fase 4):   135 premios × 1 stock c/u  =   135 unidades  (iPhone, etc.)
  Total: 4.835 premios

Uso:
  cd backend
  python -m alembic.seeds.seed_prizes
  # o con DB_URL explícita:
  DB_URL=postgresql+psycopg://... python -m alembic.seeds.seed_prizes
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Permite ejecutar desde la raíz del backend sin instalar el paquete
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+psycopg://mp_user:mp_pass@localhost:5432/mp_billete_dorado",
)

# ---------------------------------------------------------------------------
# Catálogo de premios
# unlock_at: fase mínima necesaria para que el premio sea elegible (1-4)
# ---------------------------------------------------------------------------
PRIZES: list[dict] = []

# FASE 1 — Premios pequeños (siempre disponibles desde el arranque)
for i in range(1, 3_001):
    PRIZES.append({
        "name": f"Premio pequeño #{i:04d}",
        "description": "Vale de descuento 10% en MainPaper",
        "category": "small",
        "total_quantity": 1,
        "remaining_quantity": 1,
        "is_active": True,
        "unlock_at": 1,
    })

# FASE 2 — Premios medios (se desbloquean al 25%)
for i in range(1, 901):
    PRIZES.append({
        "name": f"Premio mediano #{i:03d}",
        "description": "Vale de descuento 25% en MainPaper + envío gratis",
        "category": "medium",
        "total_quantity": 1,
        "remaining_quantity": 1,
        "is_active": True,
        "unlock_at": 2,
    })

# FASE 3 — Premios medios adicionales (se desbloquean al 50%)
for i in range(1, 601):
    PRIZES.append({
        "name": f"Premio mediano plus #{i:03d}",
        "description": "Suscripción anual MainPaper Premium",
        "category": "medium",
        "total_quantity": 1,
        "remaining_quantity": 1,
        "is_active": True,
        "unlock_at": 3,
    })

# FASE 3 — Premios especiales (iPad, becas — se desbloquean al 50%)
_special_phase3 = [
    ("iPad 10ª generación", "iPad 10th Gen 64GB WiFi"),
    ("Beca formación online", "Acceso 1 año a plataforma formativa MainPaper"),
]
for idx in range(100):
    entry = _special_phase3[idx % len(_special_phase3)]
    PRIZES.append({
        "name": f"{entry[0]} #{idx + 1:03d}",
        "description": entry[1],
        "category": "special",
        "total_quantity": 1,
        "remaining_quantity": 1,
        "is_active": True,
        "unlock_at": 3,
    })

# FASE 4 — Premios especiales top (iPhone, experiencias — se desbloquean al 75%)
_special_phase4 = [
    ("iPhone 16 Pro", "iPhone 16 Pro 128GB"),
    ("Experiencia gastronómica", "Cena para 2 en restaurante seleccionado"),
    ("Pack viaje fin de semana", "Escapada 2 noches hotel 4* en España"),
]
for idx in range(135):
    entry = _special_phase4[idx % len(_special_phase4)]
    PRIZES.append({
        "name": f"{entry[0]} #{idx + 1:03d}",
        "description": entry[1],
        "category": "special",
        "total_quantity": 1,
        "remaining_quantity": 1,
        "is_active": True,
        "unlock_at": 4,
    })

assert len(PRIZES) == 4_835, f"Total esperado 4835, obtenido {len(PRIZES)}"

BATCH_SIZE = 500


async def seed(session: AsyncSession) -> None:
    # Verificar si ya hay datos para evitar doble seed
    result = await session.execute(text("SELECT COUNT(*) FROM prizes"))
    existing = result.scalar_one()
    if existing > 0:
        print(f"[seed_prizes] Ya existen {existing} premios — omitiendo seed.")
        return

    total_inserted = 0
    for start in range(0, len(PRIZES), BATCH_SIZE):
        batch = PRIZES[start: start + BATCH_SIZE]
        await session.execute(
            text(
                "INSERT INTO prizes (name, description, category, total_quantity, "
                "remaining_quantity, is_active, unlock_at) VALUES "
                + ", ".join(
                    f"(:name_{i}, :desc_{i}, :cat_{i}, :total_{i}, "
                    f":remaining_{i}, :active_{i}, :unlock_{i})"
                    for i in range(len(batch))
                )
            ),
            {
                param: val
                for i, row in enumerate(batch)
                for param, val in {
                    f"name_{i}": row["name"],
                    f"desc_{i}": row["description"],
                    f"cat_{i}": row["category"],
                    f"total_{i}": row["total_quantity"],
                    f"remaining_{i}": row["remaining_quantity"],
                    f"active_{i}": row["is_active"],
                    f"unlock_{i}": row["unlock_at"],
                }.items()
            },
        )
        total_inserted += len(batch)
        print(f"[seed_prizes] Insertados {total_inserted}/{len(PRIZES)}...")

    await session.commit()
    print(f"[seed_prizes] Seed completado: {total_inserted} premios insertados.")


async def main() -> None:
    engine = create_async_engine(DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
