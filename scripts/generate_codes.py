"""
Genera 45.000 códigos sintéticos únicos en formato MP-XXXX-XXXX-XXXX y los
exporta a CSV. No requiere conexión a base de datos — útil para preparar el
archivo antes de importarlo vía POST /api/v1/admin/codes/import.

Uso:
    python scripts/generate_codes.py                        # → codes_45000.csv
    python scripts/generate_codes.py --count 100            # prueba rápida
    python scripts/generate_codes.py --output mi_lote.csv
"""
import argparse
import csv
import random
import string
import time
from pathlib import Path

TOTAL_CODES = 45_000
ALPHABET = string.ascii_uppercase + string.digits  # A-Z + 0-9
SEGMENT_LENGTH = 4
SEGMENT_COUNT = 3  # MP-XXXX-XXXX-XXXX → 3 segmentos de 4


def generate_code() -> str:
    segments = [
        "".join(random.choices(ALPHABET, k=SEGMENT_LENGTH))
        for _ in range(SEGMENT_COUNT)
    ]
    return "MP-" + "-".join(segments)


def generate_unique_codes(count: int) -> list[str]:
    codes: set[str] = set()
    while len(codes) < count:
        codes.add(generate_code())
    return list(codes)


def write_csv(codes: list[str], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code"])
        for code in codes:
            writer.writerow([code])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera códigos MP Billete Dorado y los exporta a CSV"
    )
    parser.add_argument(
        "--count", type=int, default=TOTAL_CODES,
        help=f"Número de códigos a generar (default: {TOTAL_CODES})",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Ruta del archivo CSV de salida (default: codes_<count>.csv)",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else Path(f"codes_{args.count}.csv")

    print(f"Generando {args.count:,} códigos únicos...")
    start = time.perf_counter()
    codes = generate_unique_codes(args.count)
    elapsed = time.perf_counter() - start

    write_csv(codes, output_path)

    print(f"  Generados en {elapsed:.2f}s")
    print(f"  Ejemplo: {codes[0]}")
    print(f"  CSV guardado en: {output_path.resolve()}")
    print(f"  Total filas: {len(codes):,}")


if __name__ == "__main__":
    main()
