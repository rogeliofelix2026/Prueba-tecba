"""Elimina entradas de caché USIG expiradas por lotes para controlar crecimiento."""

from __future__ import annotations

import argparse
import logging

from app.core.database import close_sync_pool, open_sync_pool, sync_connection

parser = argparse.ArgumentParser(description="Limpia caché USIG expirado.")
parser.add_argument("--batch-size", type=int, default=1000)


def main() -> None:
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size debe ser mayor que 0")

    logging.basicConfig(level="INFO")
    open_sync_pool()
    total = 0
    try:
        # El repository es async para la API; aquí ejecutamos una limpieza sencilla usando una
        # conexión sincrónica para que el mantenimiento no dependa del event loop.
        with sync_connection() as conn, conn.cursor() as cur:
            while True:
                cur.execute(
                    """
                    DELETE FROM geocoding_cache
                    WHERE id IN (
                        SELECT id
                        FROM geocoding_cache
                        WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                        ORDER BY expires_at
                        LIMIT %s
                    )
                    """,
                    (args.batch_size,),
                )
                deleted = cur.rowcount
                total += deleted
                if deleted < args.batch_size:
                    break
        print(f"Entradas expiradas eliminadas: {total}")
    finally:
        close_sync_pool()


if __name__ == "__main__":
    main()
