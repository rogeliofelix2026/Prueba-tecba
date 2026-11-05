"""Ingiere el Relevamiento de Usos del Suelo (RUS) en el modelo MVP.

El CSV original permanece fuera de PostgreSQL. Solo se normalizan los campos
utilizados por el análisis contextual y la relación con parcelas.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from app.core.database import close_sync_pool, open_sync_pool, sync_connection

REQUIRED_HEADERS = frozenset({"OBJECTID", "TIPO1", "TIPO2", "ESTADO", "PISOS", "OBS", "AÑO"})
OPTIONAL_HEADERS = frozenset({"SMP"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("rus",))
    parser.add_argument("csv", type=Path)
    parser.add_argument("--source-version-id", type=int, required=True)
    return parser.parse_args()


def validate_headers(fieldnames: list[str] | None) -> None:
    if not fieldnames:
        raise ValueError("El CSV no contiene headers.")
    duplicates = [name for name, count in Counter(fieldnames).items() if count > 1]
    if duplicates:
        raise ValueError(f"Headers duplicados: {sorted(duplicates)}")
    missing = REQUIRED_HEADERS - set(fieldnames)
    if missing:
        raise ValueError(f"Columnas faltantes: {sorted(missing)}")


def load_staging(cur: Any, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        validate_headers(reader.fieldnames)
        with cur.copy("COPY staging_rus(payload) FROM STDIN") as copy:
            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"Fila {row_number}: más valores que columnas del header.")
                clean_payload = {
                    key: (value.strip() if value and value.strip() else None)
                    for key, value in row.items()
                }
                copy.write_row([Jsonb(clean_payload)])


def validate_duplicates(cur: Any) -> None:
    cur.execute(
        """
        SELECT payload->>'OBJECTID' AS source_record_id, COUNT(*)
        FROM staging_rus
        WHERE NULLIF(BTRIM(payload->>'OBJECTID'), '') IS NOT NULL
        GROUP BY 1
        HAVING COUNT(*) > 1
        LIMIT 10
        """
    )
    duplicates = cur.fetchall()
    if duplicates:
        raise ValueError(f"OBJECTID duplicados en el archivo: {duplicates}")


def publish(cur: Any, source_version_id: int) -> int:
    cur.execute(
        """
        INSERT INTO land_use_observations(
            source_record_id,
            parcel_id,
            source_version_id,
            tipo1,
            tipo2,
            estado,
            pisos,
            obs,
            anio
        )
        SELECT
            (NULLIF(BTRIM(s.payload->>'OBJECTID'), ''))::BIGINT,
            p.id,
            %s,
            NULLIF(BTRIM(s.payload->>'TIPO1'), ''),
            NULLIF(BTRIM(s.payload->>'TIPO2'), ''),
            NULLIF(BTRIM(s.payload->>'ESTADO'), ''),
            NULLIF(BTRIM(s.payload->>'PISOS'), ''),
            NULLIF(BTRIM(s.payload->>'OBS'), ''),
            (NULLIF(BTRIM(s.payload->>'AÑO'), ''))::SMALLINT
        FROM staging_rus s
        LEFT JOIN parcels p
          ON p.smp = CASE
              WHEN NULLIF(BTRIM(s.payload->>'SMP'), '') IS NULL THEN NULL
              ELSE LPAD(SPLIT_PART(REGEXP_REPLACE(UPPER(BTRIM(s.payload->>'SMP')), '\\s*[-–—]\\s*', '-', 'g'), '-', 1), 3, '0')
                   || '-' || SPLIT_PART(REGEXP_REPLACE(UPPER(BTRIM(s.payload->>'SMP')), '\\s*[-–—]\\s*', '-', 'g'), '-', 2)
                   || '-' || SPLIT_PART(REGEXP_REPLACE(UPPER(BTRIM(s.payload->>'SMP')), '\\s*[-–—]\\s*', '-', 'g'), '-', 3)
          END
        WHERE NULLIF(BTRIM(s.payload->>'OBJECTID'), '') IS NOT NULL
        ON CONFLICT(source_version_id, source_record_id) DO UPDATE SET
            parcel_id = EXCLUDED.parcel_id,
            tipo1 = EXCLUDED.tipo1,
            tipo2 = EXCLUDED.tipo2,
            estado = EXCLUDED.estado,
            pisos = EXCLUDED.pisos,
            obs = EXCLUDED.obs,
            anio = EXCLUDED.anio
        """,
        (source_version_id,),
    )
    return cur.rowcount


def main() -> None:
    args = parse_args()
    if not args.csv.is_file():
        raise FileNotFoundError(args.csv)
    if args.source_version_id <= 0:
        raise ValueError("--source-version-id debe ser mayor que 0.")

    open_sync_pool()
    try:
        with sync_connection() as conn, conn.cursor() as cur:
            cur.execute("CREATE TEMP TABLE staging_rus (payload JSONB) ON COMMIT DROP")
            load_staging(cur, args.csv)
            validate_duplicates(cur)
            processed = publish(cur, args.source_version_id)
            conn.commit()
    finally:
        close_sync_pool()

    print(f"RUS ingerido: {processed} registros.")
    print(f"Source version: {args.source_version_id}")


if __name__ == "__main__":
    main()
