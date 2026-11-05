"""Persistencia del cache de geocodificación de USIG según el schema MVP final."""

from __future__ import annotations

import re
from typing import Any

from psycopg.types.json import Jsonb

from app.core.database import connection
from app.core.smp import normalize_smp


def extract_smp(payload: dict[str, Any]) -> str | None:
    """
    Obtiene un SMP válido desde el payload de USIG.

    Prioridad:
    1. payload["smp"]
    2. response_json["reverse_geocoding"]["parcela"]

    Retorna None si USIG no permite determinar un SMP válido.
    """
    response_json = payload.get("response_json") or {}

    # 1. SMP recibido directamente.
    smp = normalize_smp(payload.get("smp"))

    if smp:
        return smp

    # 2. Fallback: parcela informada por reverse geocoding.
    if isinstance(response_json, dict):
        reverse = response_json.get("reverse_geocoding")

        if isinstance(reverse, dict):
            smp = normalize_smp(reverse.get("parcela"))

            if smp:
                return smp

    return None


def extract_coordinates(
    payload: dict[str, Any],
) -> tuple[float, float] | None:
    """
    Obtiene latitude/longitude del payload.

    Prioridad:
    1. payload["latitude"], payload["longitude"]
    2. response_json["wgs84"]["resultado"]
    """
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")

    try:
        if latitude is not None and longitude is not None:
            return float(latitude), float(longitude)
    except (TypeError, ValueError):
        pass

    response_json = payload.get("response_json") or {}

    if not isinstance(response_json, dict):
        return None

    wgs84 = response_json.get("wgs84")

    if not isinstance(wgs84, dict):
        return None

    resultado = wgs84.get("resultado")

    if not isinstance(resultado, dict):
        return None

    try:
        longitude = float(resultado["x"])
        latitude = float(resultado["y"])
    except (KeyError, TypeError, ValueError):
        return None

    return latitude, longitude


class GeocodingRepository:
    """Persistencia del cache de geocodificación de USIG."""

    async def _resolve_parcel_id(
        self,
        cur: Any,
        smp: str | None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> tuple[int, str] | None:
        """
        Resuelve public.parcels.id.

        Estrategia:
        1. Buscar SMP canónico por igualdad exacta.
        2. Buscar variante de sección sin padding, para datos legacy.
        3. Como último recurso, resolver espacialmente.

        Retorna:
            (parcel_id, canonical_smp)
        """

        normalized_smp = normalize_smp(smp)

        if normalized_smp:
            # ---------------------------------------------------------------
            # 1. Búsqueda exacta: caso normal.
            #    Esta consulta puede aprovechar un índice sobre parcels.smp.
            # ---------------------------------------------------------------
            await cur.execute(
                """
                SELECT
                    p.id,
                    p.smp
                FROM public.parcels p
                WHERE p.smp = %s
                ORDER BY p.source_version_id DESC, p.id
                LIMIT 1
                """,
                (normalized_smp,),
            )

            parcel_row = await cur.fetchone()

            if parcel_row:
                parcel_smp = normalize_smp(parcel_row[1]) or normalized_smp
                return int(parcel_row[0]), parcel_smp

            # ---------------------------------------------------------------
            # 2. Compatibilidad con formato legacy:
            #    009-069-012 ↔ 09-069-012
            #
            #    Generamos la variante en Python para que PostgreSQL siga
            #    pudiendo utilizar el índice de parcels.smp.
            # ---------------------------------------------------------------
            parts = normalized_smp.split("-")

            if len(parts) == 3 and parts[0].startswith("0"):
                legacy_section = str(int(parts[0]))
                legacy_smp = f"{legacy_section}-{parts[1]}-{parts[2]}"

                if legacy_smp != normalized_smp:
                    await cur.execute(
                        """
                        SELECT
                            p.id,
                            p.smp
                        FROM public.parcels p
                        WHERE p.smp = %s
                        ORDER BY p.source_version_id DESC, p.id
                        LIMIT 1
                        """,
                        (legacy_smp,),
                    )

                    parcel_row = await cur.fetchone()

                    if parcel_row:
                        parcel_smp = normalize_smp(parcel_row[1]) or normalized_smp
                        return int(parcel_row[0]), parcel_smp

        # ---------------------------------------------------------------
        # 3. Resolución espacial estricta e indexable: el punto debe quedar
        #    cubierto por exactamente un polígono. Consultamos cada tabla
        #    geométrica directamente para que el índice GiST pueda operar;
        #    evitar LATERAL + COALESCE sobre todas las parcelas es importante
        #    para datasets catastrales de cientos de miles de filas.
        # ---------------------------------------------------------------
        if latitude is None or longitude is None:
            return None

        await cur.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema='public'
              AND ((table_name='parcels' AND column_name IN ('geometry','geom'))
                OR (table_name='parcel_geometries' AND column_name IN ('geometry','geom','parcel_id','smp')))
            """
        )
        geometry_columns: dict[str, set[str]] = {}
        for table_name, column_name in await cur.fetchall():
            geometry_columns.setdefault(str(table_name), set()).add(str(column_name))

        relations: list[tuple[str, str, str]] = []
        direct_col = next((column for column in ("geometry", "geom") if column in geometry_columns.get("parcels", set())), None)
        if direct_col:
            relations.append(("public.parcels p", f"p.{direct_col}", "p.smp"))

        cache_cols = geometry_columns.get("parcel_geometries", set())
        cache_geometry = next((column for column in ("geom", "geometry") if column in cache_cols), None)
        if cache_geometry:
            if "parcel_id" in cache_cols:
                relations.append((
                    "public.parcel_geometries pg JOIN public.parcels p ON p.id = pg.parcel_id",
                    f"pg.{cache_geometry}", "p.smp",
                ))
            elif "smp" in cache_cols:
                relations.append((
                    "public.parcel_geometries pg JOIN public.parcels p ON p.smp = pg.smp",
                    f"pg.{cache_geometry}", "p.smp",
                ))

        if not relations:
            return None

        resolved: dict[tuple[int, str], None] = {}
        for relation, geometry_expr, smp_expr in relations:
            await cur.execute(
                f"""
                WITH input_point AS (
                    SELECT ST_SetSRID(ST_MakePoint(%s, %s), 4326) AS geom
                )
                SELECT p.id, {smp_expr}
                FROM {relation}
                CROSS JOIN input_point ip
                WHERE {geometry_expr} IS NOT NULL
                  AND {geometry_expr} && ip.geom
                  AND ST_Covers({geometry_expr}, ip.geom)
                ORDER BY {smp_expr}
                LIMIT 100
                """,
                (longitude, latitude),
            )
            for row in await cur.fetchall():
                if row[0] is not None and row[1] is not None:
                    resolved[(int(row[0]), str(row[1]))] = None

        # Ningún punto fuera del lote debe convertirse en una selección legal.
        # Si dos geometrías lo cubren (p. ej. un límite), se exige una selección
        # catastral explícita en lugar de escoger arbitrariamente.
        if len(resolved) != 1:
            return None
        parcel_id, raw_smp = next(iter(resolved))
        parcel_smp = normalize_smp(raw_smp)
        return (parcel_id, parcel_smp) if parcel_smp else None

    async def get(
    self,
    query_key: str,
    provider: str = "USIG",
    ) -> dict[str, Any] | None:
        del provider

        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    gc.query_key,
                    gc.input_address,
                    gc.normalized_street,
                    gc.street_code,
                    gc.height,
                    gc.latitude,
                    gc.longitude,
                    gc.smp,
                    gc.resolved_parcel_id,
                    gc.response_json,
                    gc.expires_at,
                    gc.source_version_id
                FROM public.geocoding_cache gc
                JOIN public.source_versions sv
                ON sv.id = gc.source_version_id
                JOIN public.sources s
                ON s.id = sv.source_id
                WHERE gc.query_key = %s
                AND s.code = 'usig'
                AND sv.status = 'active'
                AND (
                    gc.expires_at IS NULL
                    OR gc.expires_at > NOW()
                )
                ORDER BY gc.fetched_at DESC
                LIMIT 1
                """,
                (query_key,),
            )

            row = await cur.fetchone()

            if row is None:
                return None

            response_json = row[9] or {}

            smp = normalize_smp(row[7])

            if not smp:
                smp = extract_smp(
                    {
                        "smp": None,
                        "response_json": response_json,
                    }
                )

            if not smp:
                raise ValueError(
                    "El registro de geocoding_cache no contiene un SMP válido: "
                    f"query_key={query_key!r}"
                )

            resolved_parcel_id = row[8]

            # Solo hacemos esta consulta en registros antiguos/incompletos.
            if resolved_parcel_id is None:
                coordinates = extract_coordinates(
                    {
                        "latitude": row[5],
                        "longitude": row[6],
                        "response_json": response_json,
                    }
                )

                latitude = coordinates[0] if coordinates else None
                longitude = coordinates[1] if coordinates else None

                resolved = await self._resolve_parcel_id(
                    cur,
                    smp,
                    latitude,
                    longitude,
                )

                if resolved is None:
                    raise ValueError(
                        "No se pudo resolver una parcela para el SMP "
                        f"{smp!r}. query_key={query_key!r}"
                    )

                resolved_parcel_id, resolved_smp = resolved
                smp = resolved_smp

                await cur.execute(
                    """
                    UPDATE public.geocoding_cache
                    SET
                        smp = %s,
                        resolved_parcel_id = %s
                    WHERE query_key = %s
                    AND source_version_id = %s
                    """,
                    (
                        smp,
                        resolved_parcel_id,
                        query_key,
                        row[11],
                    ),
                )

            elif normalize_smp(row[7]) != smp:
                await cur.execute(
                    """
                    UPDATE public.geocoding_cache
                    SET smp = %s
                    WHERE query_key = %s
                    AND source_version_id = %s
                    """,
                    (
                        smp,
                        query_key,
                        row[11],
                    ),
                )

            return {
                "query_key": row[0],
                "input_address": row[1],
                "normalized_street": row[2],
                "street_code": row[3],
                "height": row[4],
                "latitude": row[5],
                "longitude": row[6],
                "smp": smp,
                "resolved_parcel_id": resolved_parcel_id,
                "response_json": response_json,
                "expires_at": row[10],
                "source_version_id": row[11],
            }

    async def upsert(
        self,
        payload: dict[str, Any],
        ttl_hours: int,
    ) -> int | None:
        """
        Inserta o actualiza un registro del cache.

        Garantías:
        - SMP válido obligatorio.
        - resolved_parcel_id obligatorio.
        - source_version_id activo obligatorio.
        - Nunca persiste deliberadamente una fila incompleta.
        """
        if ttl_hours <= 0:
            raise ValueError("ttl_hours debe ser mayor que 0")

        response_json = payload.get("response_json") or {}

        # ---------------------------------------------------------------
        # Extraer SMP
        # ---------------------------------------------------------------
        smp = extract_smp(payload)

        coordinates = extract_coordinates(payload)

        latitude = coordinates[0] if coordinates else payload.get("latitude")
        longitude = coordinates[1] if coordinates else payload.get("longitude")

        async with connection() as conn, conn.cursor() as cur:

            # -----------------------------------------------------------
            # Resolver parcela
            # -----------------------------------------------------------
            resolved = await self._resolve_parcel_id(
                cur,
                smp,
                latitude,
                longitude,
            )

            if resolved is None:
                raise ValueError(
                    "No se pudo resolver una parcela para el SMP "
                    f"{smp!r}. No se puede persistir el cache."
                )

            resolved_parcel_id, resolved_smp = resolved

            # Siempre usamos el SMP que efectivamente representa la parcela
            # encontrada en la BD.
            smp = resolved_smp

            # -----------------------------------------------------------
            # Obtener source_version activa de USIG
            # -----------------------------------------------------------
            await cur.execute(
                """
                SELECT sv.id
                FROM public.source_versions sv
                JOIN public.sources s
                  ON s.id = sv.source_id
                WHERE s.code = 'usig'
                  AND sv.status = 'active'
                ORDER BY sv.id DESC
                LIMIT 1
                """
            )

            source_row = await cur.fetchone()

            if source_row is None:
                raise ValueError(
                    "No existe una source_version activa para USIG."
                )

            source_version_id = source_row[0]

            params = {
                **payload,
                "smp": smp,
                "resolved_parcel_id": resolved_parcel_id,
                "response_json": Jsonb(response_json),
                "source_version_id": source_version_id,
                "ttl_hours": ttl_hours,
            }

            await cur.execute(
                """
                INSERT INTO public.geocoding_cache (
                    query_key,
                    input_address,
                    normalized_street,
                    street_code,
                    height,
                    latitude,
                    longitude,
                    smp,
                    resolved_parcel_id,
                    response_json,
                    fetched_at,
                    expires_at,
                    source_version_id
                )
                VALUES (
                    %(query_key)s,
                    %(input_address)s,
                    %(normalized_street)s,
                    %(street_code)s,
                    %(height)s,
                    %(latitude)s,
                    %(longitude)s,
                    %(smp)s,
                    %(resolved_parcel_id)s,
                    %(response_json)s,
                    NOW(),
                    NOW() + (
                        %(ttl_hours)s * INTERVAL '1 hour'
                    ),
                    %(source_version_id)s
                )
                ON CONFLICT (source_version_id, query_key)
                DO UPDATE SET
                    input_address = EXCLUDED.input_address,
                    normalized_street = EXCLUDED.normalized_street,
                    street_code = EXCLUDED.street_code,
                    height = EXCLUDED.height,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    smp = EXCLUDED.smp,
                    resolved_parcel_id = EXCLUDED.resolved_parcel_id,
                    response_json = EXCLUDED.response_json,
                    fetched_at = NOW(),
                    expires_at = EXCLUDED.expires_at
                RETURNING source_version_id
                """,
                params,
            )

            row = await cur.fetchone()

        return int(row[0]) if row else None

    async def update_smp(
        self,
        query_key: str,
        provider: str,
        smp: str,
    ) -> None:
        """
        Actualiza SMP y resolved_parcel_id de un registro existente.

        El SMP se normaliza al formato canónico y la parcela se resuelve
        antes de ejecutar el UPDATE.
        """
        del provider

        normalized_smp = normalize_smp(smp)

        if normalized_smp is None:
            raise ValueError(f"SMP inválido: {smp!r}")

        async with connection() as conn, conn.cursor() as cur:

            resolved = await self._resolve_parcel_id(
                cur,
                normalized_smp,
            )

            if resolved is None:
                raise ValueError(
                    "No existe una parcela para el SMP "
                    f"{normalized_smp!r}."
                )

            resolved_parcel_id, resolved_smp = resolved

            await cur.execute(
                """
                UPDATE public.geocoding_cache gc
                SET
                    smp = %s,
                    resolved_parcel_id = %s,
                    response_json = jsonb_set(
                        COALESCE(
                            gc.response_json,
                            '{}'::jsonb
                        ),
                        '{smp}',
                        to_jsonb(%s::text),
                        true
                    ),
                    fetched_at = NOW()
                FROM public.source_versions sv
                JOIN public.sources s
                  ON s.id = sv.source_id
                WHERE gc.query_key = %s
                  AND gc.source_version_id = sv.id
                  AND s.code = 'usig'
                  AND sv.status = 'active'
                """,
                (
                    resolved_smp,
                    resolved_parcel_id,
                    resolved_smp,
                    query_key,
                ),
            )

    async def delete_expired(
        self,
        limit: int = 1000,
    ) -> int:
        """Elimina registros expirados del cache en lotes."""
        if limit < 1:
            raise ValueError("limit debe ser mayor que 0")

        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM public.geocoding_cache
                WHERE id IN (
                    SELECT id
                    FROM public.geocoding_cache
                    WHERE expires_at IS NOT NULL
                      AND expires_at <= NOW()
                    ORDER BY expires_at
                    LIMIT %s
                )
                """,
                (limit,),
            )

            return cur.rowcount