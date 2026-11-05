"""
Audita un archivo CSV antes de incorporarlo al pipeline.

Reporta:
- cantidad de registros
- columnas
- columnas duplicadas en el header
- columnas faltantes/vacías
- columnas adicionales
- nulos por columna
- espacios en blanco
- duplicados de una o más claves
- claves incompletas

Ejemplos:

    python scripts/audit_csv.py archivo.csv

    python scripts/audit_csv.py archivo.csv --key SMP

    python scripts/audit_csv.py archivo.csv --key SMP --key BARRIO
"""

import argparse
import csv
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audita la estructura y calidad básica de un CSV.")

    parser.add_argument(
        "file",
        type=Path,
        help="Ruta al archivo CSV.",
    )

    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help=(
            "Columna utilizada para detectar duplicados. "
            "Puede repetirse para formar una clave compuesta."
        ),
    )

    return parser.parse_args()


def normalize(value: str | None) -> str | None:
    """
    Normaliza un valor del CSV.

    Convierte:
        None -> None
        ""   -> None
        "   " -> None

    Mantiene el resto como string sin modificar semánticamente.
    """
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def find_duplicate_headers(fieldnames: list[str] | None) -> list[str]:
    """Devuelve headers repetidos."""
    if not fieldnames:
        return []

    counts = Counter(fieldnames)

    return sorted(column for column, count in counts.items() if count > 1)


def main() -> None:
    args = parse_args()

    if not args.file.exists():
        raise FileNotFoundError(f"No existe el archivo: {args.file}")

    if not args.file.is_file():
        raise ValueError(f"La ruta no corresponde a un archivo: {args.file}")

    with args.file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fh:
        reader = csv.DictReader(fh)

        fieldnames = reader.fieldnames or []

        if not fieldnames:
            raise ValueError("El CSV no contiene un header válido.")

        duplicate_headers = find_duplicate_headers(fieldnames)

        unknown_keys = [key for key in args.key if key not in fieldnames]

        if unknown_keys:
            raise ValueError(f"Las columnas indicadas en --key no existen: {sorted(unknown_keys)}")

        rows = 0
        nulls = Counter()
        blanks = Counter()

        key_values: list[tuple[str | None, ...]] = []
        incomplete_keys = 0

        for row_number, row in enumerate(reader, start=2):
            rows += 1

            # DictReader utiliza None como key cuando existen
            # más valores que columnas declaradas.
            if None in row:
                raise ValueError(
                    f"Fila {row_number}: contiene más valores que columnas en el header."
                )

            for column, value in row.items():
                if value is None or value.strip() == "":
                    nulls[column] += 1

                    if value == "":
                        blanks[column] += 1

            if args.key:
                normalized_key = tuple(normalize(row.get(column)) for column in args.key)

                if any(value is None for value in normalized_key):
                    incomplete_keys += 1
                else:
                    key_values.append(normalized_key)

    key_counter = Counter(key_values)

    duplicate_groups = sum(1 for count in key_counter.values() if count > 1)

    duplicate_extra_rows = sum(count - 1 for count in key_counter.values() if count > 1)

    print(f"Archivo: {args.file}")
    print(f"Registros: {rows}")
    print(f"Columnas: {fieldnames}")

    if duplicate_headers:
        print(f"Headers duplicados: {duplicate_headers}")
    else:
        print("Headers duplicados: []")

    print(f"Nulos/vacíos: {dict(nulls)}")

    if blanks:
        print(f"Cadenas vacías: {dict(blanks)}")

    if args.key:
        print(f"Clave auditada: {args.key}")
        print(f"Claves incompletas: {incomplete_keys}")
        print(f"Grupos de claves duplicadas: {duplicate_groups}")
        print(f"Registros duplicados adicionales: {duplicate_extra_rows}")


if __name__ == "__main__":
    main()
