"""
Genera e inserta 45.000 códigos únicos con formato MP-XXXX-XXXX-XXXX
en la tabla `codes`. Cada X es un carácter alfanumérico mayúscula/número.

Uso:
    DATABASE_URL=postgresql+psycopg2://... python scripts/load_codes.py
    DATABASE_URL=... python scripts/load_codes.py --sample 100   # prueba
"""
import argparse
import os
import random
import string
import time
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

TOTAL_CODES = 45_000
ALPHABET = string.ascii_uppercase + string.digits  # A-Z + 0-9
BATCH_SIZE = 1_000
SEGMENT_LENGTH = 4
SEGMENT_COUNT = 3  # MP-XXXX-XXXX-XXXX → 3 segmentos de 4


def generate_code() -> str:
    segments = ["".join(random.choices(ALPHABET, k=SEGMENT_LENGTH)) for _ in range(SEGMENT_COUNT)]
    return "MP-" + "-".join(segments)


def generate_unique_codes(count: int) -> list[str]:
    """Genera `count` códigos sin duplicados en memoria antes de insertar."""
    codes: set[str] = set()
    while len(codes) < count:
        codes.add(generate_code())
    return list(codes)


@contextmanager
def get_connection(database_url: str):
    # psycopg2 usa postgresql://, no postgresql+asyncpg://
    url = database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )
    conn = psycopg2.connect(url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_codes(database_url: str, count: int) -> None:
    print(f"Generando {count:,} códigos únicos...")
    start = time.perf_counter()
    codes = generate_unique_codes(count)
    elapsed_gen = time.perf_counter() - start
    print(f"  Generados en {elapsed_gen:.2f}s — ejemplo: {codes[0]}")

    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            # Verifica que la tabla existe antes de insertar
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'codes')")
            if not cur.fetchone()[0]:
                raise RuntimeError("La tabla 'codes' no existe. Ejecuta las migraciones Alembic primero.")

            inserted = 0
            skipped = 0
            start_insert = time.perf_counter()

            for batch_start in range(0, len(codes), BATCH_SIZE):
                batch = codes[batch_start : batch_start + BATCH_SIZE]
                rows = [(code, "unused") for code in batch]

                # ON CONFLICT DO NOTHING garantiza unicidad sin error si hay colisión residual
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO codes (code, status) VALUES %s ON CONFLICT (code) DO NOTHING",
                    rows,
                )
                inserted += cur.rowcount
                skipped += len(batch) - cur.rowcount
                print(f"  Lote {batch_start // BATCH_SIZE + 1}: {inserted:,} insertados, {skipped} omitidos")

    elapsed_total = time.perf_counter() - start
    print(f"\nFinalizado: {inserted:,} códigos insertados, {skipped} omitidos (duplicados)")
    print(f"Tiempo total: {elapsed_total:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga códigos MP Billete Dorado en la base de datos")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Insertar solo N códigos de muestra (por defecto: 45.000)",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("ERROR: la variable DATABASE_URL no está definida")

    count = args.sample if args.sample else TOTAL_CODES
    load_codes(database_url, count)


if __name__ == "__main__":
    main()
