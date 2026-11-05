"""Repositorio territorial compatible con el esquema compacto y variantes legacy.

La parcela canónica se resuelve por SMP. La geometría es opcional y puede residir
bien en parcels.geometry, bien en parcel_geometries como caché independiente.
Las columnas de mixtura pueden ser `mixturas SMALLINT[]` o `uso_1/uso_2/uso_3`.
El esquema se inspecciona antes de generar SQL para no convertir incompatibilidades
conocidas en errores PostgreSQL opacos.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import TYPE_CHECKING, Any

from app.core.config import settings
from app.core.smp import normalize_smp

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool


class TerritorySchemaError(RuntimeError):
    """El esquema no contiene los campos mínimos para resolver territorio."""


def canonical_smp(value: str | None) -> str | None:
    """Alias de compatibilidad; todos los componentes comparten el mismo parser."""
    return normalize_smp(value)

def _ident(value: str) -> str:
    # Solo se invoca para nombres seleccionados de information_schema y whitelist.
    return '"' + value.replace('"', '""') + '"'


class TerritoryRepository:
    """Consulta parcela, normativa, distritos y observaciones sin asumir geometría inline."""

    _TABLES = (
        "parcels", "barrios", "comunas", "urban_parcel_rules",
        "parcel_special_districts", "land_use_observations", "parcel_geometries", "query_runs", "source_versions",
        "activity_tramite_mappings", "procedure_variants", "procedures", "procedure_requirements",
        "procedure_documents", "procedure_steps", "activity_procedures", "procedure_rules",
    )

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool
        self._schema: dict[str, set[str]] | None = None
        self._schema_lock = asyncio.Lock()

    async def schema_capabilities(self, *, refresh: bool = False) -> dict[str, Any]:
        """Devuelve capacidades efectivas de la BD; útil para /ready y diagnóstico."""
        if self._schema is None or refresh:
            async with self._schema_lock:
                if self._schema is None or refresh:
                    async with self._pool.connection() as conn, conn.cursor() as cur:
                        self._schema = await self._read_schema(cur)
        schema = self._schema or {}
        parcel_cols = schema.get("parcels", set())
        cache_cols = schema.get("parcel_geometries", set())
        rule_cols = schema.get("urban_parcel_rules", set())
        direct_geometry = bool({"geometry", "geom"} & parcel_cols)
        cache_geometry = bool({"geometry", "geom"} & cache_cols) and bool({"parcel_id", "smp"} & cache_cols)
        barrios_cols = schema.get("barrios", set())
        comunas_cols = schema.get("comunas", set())
        has_barrio_name = ("barrio_id" in parcel_cols and {"id", "name"} <= barrios_cols) or "barrio" in parcel_cols
        has_comuna = (
            "comuna" in parcel_cols
            or "comuna_id" in parcel_cols
            or ("barrio_id" in parcel_cols and {"id", "comuna_id"} <= barrios_cols)
        )
        audit_cols = schema.get("query_runs", set())
        required_rule_identity = {"id", "parcel_id", "source_version_id"} <= rule_cols
        rule_payload_available = "mixturas" in rule_cols or {"uso_1", "uso_2", "uso_3"} <= rule_cols
        district_cols = schema.get("parcel_special_districts", set())
        mapping_cols = schema.get("activity_tramite_mappings", set())
        procedure_required_columns = {
            "activity_procedures": {"id", "activity_id", "procedure_id", "source_version_id"},
            "procedures": {"id", "code", "name", "source_version_id"},
            "procedure_variants": {"id", "procedure_id", "code", "name", "description", "conditions", "immediate_start_allowed", "prior_inspection_required", "validity_years", "source_version_id", "active"},
            "procedure_requirements": {"id", "procedure_id", "requirement_code", "title", "description", "conditional", "conditions", "source_version_id"},
            "procedure_documents": {"id", "procedure_id", "document_code", "title", "description", "conditional", "conditions", "source_version_id"},
            "procedure_steps": {"id", "procedure_id", "step_order", "title", "description", "source_version_id"},
            "procedure_rules": {"id", "activity_procedure_id", "rule_type", "priority", "min_surface_m2", "max_surface_m2", "conditions", "rationale", "active", "source_version_id"},
        }
        # Debe coincidir con las columnas que consume ActivityTramiteMappingRepository;
        # una tabla presente pero incompleta no puede declarar la API como ready.
        mapping_ready = {
            "activity_id", "source_version_id", "activity_code_snapshot",
            "catalog_activity_name_snapshot", "annex_ii_activity_name_verified",
            "procedure_type_code", "procedure_type_label", "possible_procedure_type_codes",
            "mapping_status", "mapping_method", "annex_ii_page", "observations", "source_annex_id",
        } <= mapping_cols
        return {
            "parcel_identity": {"table": "parcels", "available": {"id", "smp", "source_version_id"} <= parcel_cols},
            "administrative_data": bool(has_barrio_name and has_comuna),
            "urban_rules": bool(required_rule_identity and rule_payload_available),
            "geometry": "combined" if direct_geometry and cache_geometry else ("parcel_geometries" if cache_geometry else ("parcels" if direct_geometry else None)),
            "special_districts": {"parcel_id", "group_code", "special_code"} <= district_cols,
            "land_use": {"land_use_observations"} <= schema.keys(),
            "activity_tramite_mappings": mapping_ready,
            "procedure_detail_schema": all(
                required <= schema.get(table, set())
                for table, required in procedure_required_columns.items()
            ),
            "structured_query_audit": {"id", "request_id", "request_payload", "response_json", "execution_mode"} <= audit_cols,
        }

    async def resolve(
        self,
        smp: str | None,
        latitude: float | None,
        longitude: float | None,
        include_geometry: bool = False,
    ) -> dict[str, Any]:
        async with self._pool.connection() as conn, conn.cursor() as cur:
            schema = await self._get_schema(cur)
            self._validate_base_schema(schema)
            warnings: list[str] = []
            geometry_available = self._geometry_source(schema) is not None
            if include_geometry and not geometry_available:
                warnings.append("PARCEL_GEOMETRY_UNAVAILABLE")

            parcel = await self._find_parcel_by_smp(cur, schema, smp, include_geometry)
            if parcel is None and latitude is not None and longitude is not None and geometry_available:
                parcel = await self._find_parcel_by_point(cur, schema, latitude, longitude, include_geometry)
                # Una coordenada geocodificada puede quedar en la línea municipal o
                # sobre la calzada. Solo usamos proximidad como fallback explícito,
                # con umbral y diferencia mínima entre candidatos; nunca se presenta
                # como una identificación catastral confirmada.
                if parcel is None:
                    parcel = await self._find_parcel_near_point(
                        cur, schema, latitude, longitude, include_geometry,
                        max_distance_m=35.0, min_runner_up_gap_m=4.0,
                    )
                    if parcel is not None and not parcel.get("_ambiguous"):
                        warnings.append("PARCEL_RESOLVED_BY_NEAREST_GEOMETRY_REQUIRES_CONFIRMATION")
            if parcel and parcel.get("_ambiguous"):
                return {
                    "parcel": None,
                    "smp": canonical_smp(smp) or smp,
                    "urban_rules": [],
                    "land_use": [],
                    "resolution_status": "ambiguous",
                    "candidate_parcels": parcel.get("candidates", []),
                    "warnings": [*warnings, "PARCEL_MATCH_AMBIGUOUS"],
                }
            if parcel is None:
                warnings.append("PARCEL_NOT_RESOLVED")
                return {
                    "parcel": None,
                    "smp": canonical_smp(smp) or smp,
                    "urban_rules": [],
                    "land_use": [],
                    "resolution_status": "not_resolved",
                    "candidate_parcels": [],
                    "warnings": warnings,
                }

            if not parcel.get("match_method"):
                parcel["match_method"] = "smp_exact"
            parcel.setdefault("match_distance_m", None)
            parcel_id = int(parcel["id"])
            urban_rule = await self._find_urban_rule(cur, schema, parcel_id)
            if urban_rule is None:
                warnings.append("URBAN_RULE_NOT_FOUND")
            if not schema.get("parcel_special_districts"):
                warnings.append("SPECIAL_DISTRICTS_TABLE_UNAVAILABLE")
            land_use = await self._find_land_use(cur, schema, parcel_id)
            if not schema.get("land_use_observations"):
                # RUS es contexto observacional opcional: no condiciona compatibilidad legal.
                warnings.append("LAND_USE_SCHEMA_UNAVAILABLE_OPTIONAL")
            elif not land_use:
                await cur.execute("SELECT EXISTS (SELECT 1 FROM public.land_use_observations LIMIT 1)")
                dataset_has_rows = bool((await cur.fetchone() or (False,))[0])
                warnings.append(
                    "LAND_USE_NO_OBSERVATIONS_FOR_PARCEL" if dataset_has_rows else "LAND_USE_DATASET_EMPTY_OPTIONAL"
                )

            return {
                "parcel": parcel,
                "smp": parcel["smp"],
                "urban_rules": [urban_rule] if urban_rule else [],
                "land_use": land_use,
                "resolution_status": "resolved",
                "candidate_parcels": [],
                "warnings": warnings,
            }

    async def cache_geometry(
        self, parcel_id: int, geojson: dict[str, Any], source_version_id: int | None = None,
    ) -> bool:
        """Persiste una geometría puntual con procedencia de fuente verificable.

        Cuando el llamador no entrega una versión, resuelve la versión activa de la
        fuente `parcelas`. Una versión `usig` nunca se usa como origen de un polígono
        obtenido del dataset catastral.
        """
        if not isinstance(geojson, dict) or geojson.get("type") not in {"Polygon", "MultiPolygon"}:
            return False
        if not isinstance(geojson.get("coordinates"), list) or not geojson.get("coordinates"):
            return False
        geometry_json = json.dumps(geojson, separators=(",", ":"), ensure_ascii=False)
        checksum = hashlib.sha256(geometry_json.encode("utf-8")).hexdigest()
        async with self._pool.connection() as conn, conn.cursor() as cur:
            schema = await self._get_schema(cur)
            cols = schema.get("parcel_geometries", set())
            geom_col = next((col for col in ("geom", "geometry") if col in cols), None)
            if not geom_col or "parcel_id" not in cols or "source_version_id" not in cols:
                return False

            # Una versión explícita solo se acepta si pertenece a `parcelas`; si no
            # se especifica, el fallback de conveniencia usa la versión vigente.
            valid_source_version = None
            if source_version_id is not None:
                await cur.execute(
                    """SELECT sv.id FROM public.source_versions sv
                       JOIN public.sources s ON s.id = sv.source_id
                       WHERE sv.id = %s AND s.code = 'parcelas'""",
                    (source_version_id,),
                )
                row = await cur.fetchone()
                valid_source_version = int(row[0]) if row else None
                # If an explicit version was passed, reject a provenance mismatch rather
                # than silently recording a geometry under another release's ID.
                if valid_source_version is None:
                    return False
            else:
                await cur.execute(
                    """SELECT sv.id FROM public.source_versions sv
                       JOIN public.sources s ON s.id = sv.source_id
                       WHERE s.code = 'parcelas' AND sv.status IN ('active', 'ingested')
                       ORDER BY (sv.status = 'active') DESC,
                                COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                                sv.id DESC LIMIT 1"""
                )
                row = await cur.fetchone()
                valid_source_version = int(row[0]) if row else None
            if valid_source_version is None:
                return False

            loaded_col = next((col for col in ("loaded_at", "fetched_at", "updated_at", "created_at") if col in cols), None)
            checksum_col = "checksum_sha256" if "checksum_sha256" in cols else None
            insert_cols = ["parcel_id", geom_col, "source_version_id"]
            values = ["%s", "ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)), 3))", "%s"]
            params: list[Any] = [parcel_id, geometry_json, valid_source_version]
            if checksum_col:
                insert_cols.append(checksum_col)
                values.append("%s")
                params.append(checksum)
            if loaded_col:
                insert_cols.append(loaded_col)
                values.append("NOW()")
            update_parts = [
                f"{_ident(geom_col)} = EXCLUDED.{_ident(geom_col)}",
                "source_version_id = EXCLUDED.source_version_id",
            ]
            if checksum_col:
                update_parts.append(f"{_ident(checksum_col)} = EXCLUDED.{_ident(checksum_col)}")
            if loaded_col:
                update_parts.append(f"{_ident(loaded_col)} = NOW()")
            await cur.execute(
                f"INSERT INTO public.parcel_geometries ({', '.join(_ident(col) for col in insert_cols)}) "
                f"VALUES ({', '.join(values)}) ON CONFLICT (parcel_id) DO UPDATE SET {', '.join(update_parts)} RETURNING parcel_id",
                tuple(params),
            )
            return bool(await cur.fetchone())

    async def postgis_point_check(self, latitude: float, longitude: float) -> dict[str, Any]:
        async with self._pool.connection() as conn, conn.cursor() as cur:
            schema = await self._get_schema(cur)
            self._validate_base_schema(schema)
            source = self._geometry_source(schema)
            if source is None:
                return {
                    "point_valid": -90 <= latitude <= 90 and -180 <= longitude <= 180,
                    "geometry_available": False,
                    "parcels_containing": 0,
                    "matching_smps": [],
                    "warning": "PARCEL_GEOMETRY_UNAVAILABLE",
                }
            candidates = await self._geometry_candidates(cur, schema, latitude, longitude)
            smps = [item[0] for item in candidates]
        return {
            "point_valid": -90 <= latitude <= 90 and -180 <= longitude <= 180,
            "geometry_available": True,
            "parcels_containing": len(smps),
            "matching_smps": smps,
        }

    async def _get_schema(self, cur: Any) -> dict[str, set[str]]:
        if self._schema is None:
            async with self._schema_lock:
                if self._schema is None:
                    self._schema = await self._read_schema(cur)
        return self._schema

    async def _read_schema(self, cur: Any) -> dict[str, set[str]]:
        await cur.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            """,
            (list(self._TABLES) + ["activity_tramite_mappings"],),
        )
        schema: dict[str, set[str]] = {}
        for table_name, column_name in await cur.fetchall():
            schema.setdefault(str(table_name), set()).add(str(column_name))
        return schema

    @staticmethod
    def _validate_base_schema(schema: dict[str, set[str]]) -> None:
        parcel_columns = schema.get("parcels", set())
        missing = sorted({"id", "smp", "source_version_id"} - parcel_columns)
        if missing:
            raise TerritorySchemaError(
                "Schema SGI incompatible: public.parcels carece de " + ", ".join(missing)
            )

    @staticmethod
    def _geometry_source(schema: dict[str, set[str]]) -> dict[str, str] | None:
        parcel_cols = schema.get("parcels", set())
        direct_col = next((col for col in ("geometry", "geom") if col in parcel_cols), None)
        cols = schema.get("parcel_geometries", set())
        cache_geometry = next((col for col in ("geometry", "geom") if col in cols), None)
        key_column = "parcel_id" if "parcel_id" in cols else ("smp" if "smp" in cols else None)

        # Si ambas fuentes existen, preferimos la caché cuando tenga geometría,
        # pero usamos la geometría inline como fallback. Esto cubre migraciones
        # donde parcels.geometry permanece vacía después de separar el caché.
        if cache_geometry and key_column:
            source = {
                "table": "parcel_geometries", "geometry": cache_geometry,
                "key": "id", "key_column": key_column,
            }
            if direct_col:
                source["table"] = "combined"
                source["direct_geometry"] = direct_col
            return source
        if direct_col:
            return {"table": "parcels", "geometry": direct_col, "key": "id", "key_column": "id"}
        return None

    @classmethod
    def _geometry_join(cls, schema: dict[str, set[str]], source: dict[str, str] | None, *, require: bool) -> tuple[str, str]:
        if source is None:
            return "", "NULL::geometry"
        if source["table"] == "parcels":
            return "", f"p.{_ident(source['geometry'])}"
        cols = schema.get("parcel_geometries", set())
        key_col = source["key_column"]
        match_expr = f"pg.{_ident(key_col)} = " + ("p.id" if key_col == "parcel_id" else "p.smp")
        order_cols = [col for col in ("fetched_at", "updated_at", "created_at", "id") if col in cols]
        order_sql = " ORDER BY " + ", ".join(f"pg.{_ident(col)} DESC NULLS LAST" for col in order_cols) if order_cols else ""
        selected_source_version = f"pg.{_ident('source_version_id')}" if "source_version_id" in cols else "NULL::bigint"
        join_sql = f"""
            LEFT JOIN LATERAL (
                SELECT pg.{_ident(source['geometry'])} AS geometry,
                       {selected_source_version} AS source_version_id
                FROM public.parcel_geometries pg
                WHERE {match_expr}
                {order_sql}
                LIMIT 1
            ) pg_cache ON TRUE
        """
        if source["table"] == "combined":
            geometry_expr = f"COALESCE(p.{_ident(source['direct_geometry'])}, pg_cache.geometry)"
        else:
            geometry_expr = "pg_cache.geometry"
        return join_sql, geometry_expr

    async def _find_parcel_by_smp(
        self, cur: Any, schema: dict[str, set[str]], smp: str | None, include_geometry: bool,
    ) -> dict[str, Any] | None:
        canonical = canonical_smp(smp)
        if canonical is None:
            return None
        parts = canonical.split("-")
        section, block, parcel = parts
        # No reescribimos SMP almacenados: probamos igualdad indexable contra las
        # representaciones habituales de sección (p. ej. 01, 001 o 1).
        section_variants = [section, section.zfill(2), section.zfill(3), str(int(section))]
        candidates: list[str] = []
        for candidate_section in section_variants:
            candidate = f"{candidate_section}-{block}-{parcel}"
            if candidate not in candidates:
                candidates.append(candidate)

        for index, candidate in enumerate(candidates):
            direct = await self._fetch_parcels(
                cur, schema, "p.smp = %s", (candidate,), include_geometry, require_geometry=False
            )
            if direct is None:
                continue
            if not direct.get("_ambiguous"):
                direct["match_method"] = "smp_exact" if index == 0 else "smp_format_fallback"
                direct["match_distance_m"] = None
            return direct
        return None

    def _indexed_geometry_relations(self, schema: dict[str, set[str]]) -> list[tuple[str, str, str]]:
        """Devuelve (FROM/JOIN, expresión geométrica, SMP) con predicados indexables."""
        relations: list[tuple[str, str, str]] = []
        parcel_cols = schema.get("parcels", set())
        direct_col = next((col for col in ("geometry", "geom") if col in parcel_cols), None)
        if direct_col:
            relations.append(("public.parcels p", f"p.{_ident(direct_col)}", "p.smp"))

        geo_cols = schema.get("parcel_geometries", set())
        geo_col = next((col for col in ("geom", "geometry") if col in geo_cols), None)
        if geo_col:
            if "parcel_id" in geo_cols:
                relations.append((
                    "public.parcel_geometries g JOIN public.parcels p ON p.id = g.parcel_id",
                    f"g.{_ident(geo_col)}", "p.smp",
                ))
            elif "smp" in geo_cols:
                relations.append((
                    "public.parcel_geometries g JOIN public.parcels p ON p.smp = g.smp",
                    f"g.{_ident(geo_col)}", "p.smp",
                ))
        return relations

    async def _geometry_candidates(
        self, cur: Any, schema: dict[str, set[str]], latitude: float, longitude: float,
        *, nearest: bool = False, max_distance_m: float = 35.0,
    ) -> list[tuple[str, float | None]]:
        """Consulta directa sobre la tabla espacial para aprovechar el índice GiST."""
        candidates: dict[str, float | None] = {}
        point_sql = "ST_SetSRID(ST_MakePoint(%s, %s), 4326)"
        for relation, geom_expr, smp_expr in self._indexed_geometry_relations(schema):
            if nearest:
                sql = f"""
                    WITH target AS (SELECT {point_sql} AS point), nearest_candidates AS (
                        SELECT {smp_expr} AS smp,
                               ST_Distance({geom_expr}::geography, target.point::geography) AS distance_m
                        FROM {relation}
                        CROSS JOIN target
                        WHERE {geom_expr} IS NOT NULL
                          AND {geom_expr} && ST_Expand(target.point, 0.001)
                        ORDER BY {geom_expr} <-> target.point
                        LIMIT 50
                    )
                    SELECT smp, MIN(distance_m) AS distance_m
                    FROM nearest_candidates
                    WHERE distance_m <= %s
                    GROUP BY smp
                    ORDER BY MIN(distance_m), smp
                    LIMIT 10
                """
                params = (longitude, latitude, max_distance_m)
            else:
                sql = f"""
                    SELECT {smp_expr} AS smp, NULL::double precision AS distance_m
                    FROM {relation}
                    WHERE {geom_expr} IS NOT NULL
                      AND {geom_expr} && {point_sql}
                      AND ST_Covers({geom_expr}, {point_sql})
                    ORDER BY {smp_expr}
                    LIMIT 100
                """
                params = (longitude, latitude, longitude, latitude)
            await cur.execute(sql, params)
            for smp_value, distance_value in await cur.fetchall():
                if smp_value is None:
                    continue
                key = str(smp_value)
                distance = float(distance_value) if distance_value is not None else None
                if key not in candidates or (
                    distance is not None and (candidates[key] is None or distance < float(candidates[key]))
                ):
                    candidates[key] = distance
        return sorted(
            candidates.items(),
            key=lambda item: (float("inf") if item[1] is None else item[1], item[0]),
        )

    async def _find_parcel_by_point(
        self, cur: Any, schema: dict[str, set[str]], latitude: float, longitude: float, include_geometry: bool,
    ) -> dict[str, Any] | None:
        matches = await self._geometry_candidates(cur, schema, latitude, longitude)
        if not matches:
            return None
        if len(matches) > 1:
            return {
                "_ambiguous": True,
                "candidates": [{"smp": smp, "distance_m": None} for smp, _ in matches[:10]],
            }
        parcel = await self._fetch_parcels(
            cur, schema, "p.smp = %s", (matches[0][0],), include_geometry, require_geometry=False,
        )
        if parcel and not parcel.get("_ambiguous"):
            parcel["match_method"] = "point_in_polygon"
            parcel["match_distance_m"] = 0.0
        return parcel

    async def _find_parcel_near_point(
        self, cur: Any, schema: dict[str, set[str]], latitude: float, longitude: float,
        include_geometry: bool, *, max_distance_m: float, min_runner_up_gap_m: float,
    ) -> dict[str, Any] | None:
        matches = await self._geometry_candidates(
            cur, schema, latitude, longitude, nearest=True, max_distance_m=max_distance_m,
        )
        if not matches:
            return None
        if len(matches) > 1 and matches[1][1] is not None and matches[0][1] is not None:
            gap = float(matches[1][1]) - float(matches[0][1])
            if gap < min_runner_up_gap_m:
                return {
                    "_ambiguous": True,
                    "candidates": [
                        {"smp": smp, "distance_m": round(float(distance), 2) if distance is not None else None}
                        for smp, distance in matches[:5]
                    ],
                }
        smp, distance = matches[0]
        parcel = await self._fetch_parcels(
            cur, schema, "p.smp = %s", (smp,), include_geometry, require_geometry=False,
        )
        if parcel and not parcel.get("_ambiguous"):
            parcel["match_method"] = "postgis_nearest_within_threshold"
            parcel["match_distance_m"] = round(float(distance), 2) if distance is not None else None
        return parcel

    @classmethod
    def _geometry_metadata_join(cls, schema: dict[str, set[str]], source: dict[str, str] | None) -> str:
        """Lee la versión de geometría sin materializar el polígono grande."""
        if not source or source["table"] not in {"parcel_geometries", "combined"}:
            return ""
        cols = schema.get("parcel_geometries", set())
        if "source_version_id" not in cols:
            return ""
        key_col = source["key_column"]
        match_expr = f"pg.{_ident(key_col)} = " + ("p.id" if key_col == "parcel_id" else "p.smp")
        order_cols = [col for col in ("loaded_at", "fetched_at", "updated_at", "created_at", "id") if col in cols]
        order_sql = " ORDER BY " + ", ".join(f"pg.{_ident(col)} DESC NULLS LAST" for col in order_cols) if order_cols else ""
        return f"""
            LEFT JOIN LATERAL (
                SELECT pg.source_version_id
                FROM public.parcel_geometries pg
                WHERE {match_expr}{order_sql}
                LIMIT 1
            ) pg_cache ON TRUE
        """

    async def _fetch_parcels(
        self, cur: Any, schema: dict[str, set[str]], where_clause: str, params: tuple[Any, ...],
        include_geometry: bool, require_geometry: bool,
    ) -> dict[str, Any] | None:
        parcel_cols = schema.get("parcels", set())
        source = self._geometry_source(schema)
        if include_geometry or require_geometry:
            join_sql, geometry_expr = self._geometry_join(schema, source, require=require_geometry)
        else:
            # El contrato incluye la versión de la geometría aunque no se serialice;
            # esta consulta lateral recupera solo el ID de versión, no el polígono.
            join_sql = self._geometry_metadata_join(schema, source)
            geometry_expr = "NULL::geometry"
        geometry_sql = f"ST_AsGeoJSON({geometry_expr})" if include_geometry and source else "NULL::text"
        if source and source["table"] == "parcel_geometries":
            geometry_source_version_expr = "pg_cache.source_version_id"
        elif source and source["table"] == "combined":
            geometry_source_version_expr = f"CASE WHEN p.{_ident(source['direct_geometry'])} IS NULL THEN pg_cache.source_version_id ELSE NULL::bigint END"
        else:
            geometry_source_version_expr = "NULL::bigint"

        partida_expr = "p.partida_ma" if "partida_ma" in parcel_cols else "NULL"
        barrio_id_expr = "p.barrio_id" if "barrio_id" in parcel_cols else "NULL"
        barrios_cols = schema.get("barrios", set())
        comunas_cols = schema.get("comunas", set())
        can_join_barrio = "barrio_id" in parcel_cols and {"id", "name"} <= barrios_cols
        if can_join_barrio:
            direct_barrio_expr = "b.name"
        elif "barrio" in parcel_cols:
            direct_barrio_expr = "p.barrio"
        else:
            direct_barrio_expr = "NULL"
        barrio_join = "LEFT JOIN public.barrios b ON b.id = p.barrio_id" if can_join_barrio else ""
        direct_comuna_id_expr = (
            "p.comuna_id" if "comuna_id" in parcel_cols
            else "b.comuna_id" if barrio_join and "comuna_id" in schema.get("barrios", set())
            else "NULL"
        )
        direct_comuna_expr = "p.comuna" if "comuna" in parcel_cols else "c.name" if {"id", "name"} <= comunas_cols else "NULL"
        if "comuna_id" in parcel_cols and {"id", "name"} <= comunas_cols:
            comuna_join = "LEFT JOIN public.comunas c ON c.id = p.comuna_id"
        elif barrio_join and "comuna_id" in barrios_cols and {"id", "name"} <= comunas_cols:
            comuna_join = "LEFT JOIN public.comunas c ON c.id = b.comuna_id"
        else:
            comuna_join = ""
        if not comuna_join and "comuna" not in parcel_cols:
            direct_comuna_expr = "NULL"

        geometry_source_join = join_sql if source and source["table"] in {"parcel_geometries", "combined"} else ""
        sql = f"""
            SELECT p.id, p.smp, {partida_expr}, {barrio_id_expr}, {direct_barrio_expr},
                   {direct_comuna_id_expr}, {direct_comuna_expr}, p.source_version_id,
                   {geometry_sql}, {geometry_source_version_expr}
            FROM public.parcels p
            {barrio_join}
            {comuna_join}
            {geometry_source_join}
            WHERE {where_clause}
            ORDER BY p.smp
            LIMIT 2
        """
        await cur.execute(sql, params)
        rows = await cur.fetchall()
        if not rows:
            return None
        if len(rows) > 1:
            return {"_ambiguous": True, "candidates": [{"smp": row[1], "id": row[0]} for row in rows]}
        row = rows[0]
        geometry = None
        if include_geometry and row[8]:
            try:
                geometry = json.loads(row[8]) if isinstance(row[8], str) else row[8]
            except (TypeError, ValueError, json.JSONDecodeError):
                geometry = None
        return {
            "id": int(row[0]), "smp": row[1], "partida_ma": row[2],
            "barrio_id": row[3], "barrio": row[4], "comuna_id": row[5],
            "comuna": row[6], "source_version_id": row[7],
            "geometry": geometry, "geometry_source_version_id": row[9],
        }

    async def _find_urban_rule(self, cur: Any, schema: dict[str, set[str]], parcel_id: int) -> dict[str, Any] | None:
        cols = schema.get("urban_parcel_rules", set())
        if not cols or "parcel_id" not in cols:
            return None
        if "mixturas" in cols:
            mixturas_expr = "upr.mixturas"
        else:
            uses = [f"upr.{col}::smallint" if col in cols else "NULL::smallint" for col in ("uso_1", "uso_2", "uso_3")]
            mixturas_expr = f"array_remove(ARRAY[{', '.join(uses)}], NULL)"
        fields = [
            ("sm", "sm"), ("catalogado", "catalogado"), ("rh", "rh"), ("ensanche", "ensanche"),
            ("apertura", "apertura"), ("lep", "lep"), ("ci_digital", "ci_digital"), ("anac", "anac"),
        ]
        indicator_exprs = [f"upr.{_ident(col)}" if col in cols else f"NULL AS {_ident(col)}" for col, _ in fields]
        rule_id_expr = "upr.id" if "id" in cols else "NULL::bigint AS id"
        source_version_expr = "upr.source_version_id" if "source_version_id" in cols else "NULL::bigint AS source_version_id"
        order_parts: list[str] = []
        joins = ""
        where_parts = ["upr.parcel_id = %s"]
        source_version_cols = schema.get("source_versions", set())
        if "source_version_id" in cols and "source_versions" in schema:
            if "status" in source_version_cols:
                joins = " JOIN public.source_versions upr_sv ON upr_sv.id = upr.source_version_id"
                where_parts.append("upr_sv.status IN ('active', 'ingested')")
                order_parts.append("(upr_sv.status = 'active') DESC")
            effective_cols = [name for name in ("effective_from", "published_at") if name in source_version_cols]
            if effective_cols:
                if len(effective_cols) == 2:
                    order_parts.append("COALESCE(upr_sv.effective_from, upr_sv.published_at) DESC NULLS LAST")
                else:
                    order_parts.append(f"upr_sv.{_ident(effective_cols[0])} DESC NULLS LAST")
            order_parts.append("upr.source_version_id DESC NULLS LAST")
        if "id" in cols:
            order_parts.append("upr.id DESC")
        order_sql = " ORDER BY " + ", ".join(order_parts) if order_parts else ""
        select_cols = [rule_id_expr, "upr.parcel_id", f"{mixturas_expr} AS mixturas", source_version_expr, *indicator_exprs]
        where_sql = " AND ".join(where_parts)
        await cur.execute(
            f"SELECT {', '.join(select_cols)} FROM public.urban_parcel_rules upr{joins} WHERE {where_sql}{order_sql} LIMIT 1",
            (parcel_id,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        raw_mixturas = row[2] or []
        if not isinstance(raw_mixturas, (list, tuple)):
            raw_mixturas = [raw_mixturas]
        mixturas: list[int] = []
        for value in raw_mixturas:
            try:
                item = int(value)
            except (ValueError, TypeError):
                continue
            if 1 <= item <= 4 and item not in mixturas:
                mixturas.append(item)
        mixturas.sort()
        result: dict[str, Any] = {
            "id": row[0], "parcel_id": row[1], "mixturas": mixturas,
            "source_version_id": row[3], "special_districts": [],
        }
        for index, key in enumerate(("sm", "catalogado", "rh", "ensanche", "apertura", "lep", "ci_digital", "anac"), start=4):
            result[key] = row[index]
        for index, key in enumerate(("uso_1", "uso_2", "uso_3")):
            result[key] = mixturas[index] if index < len(mixturas) else None

        district_cols = schema.get("parcel_special_districts", set())
        if {"parcel_id", "group_code", "special_code"} <= district_cols:
            district_version_expr = "psd.source_version_id" if "source_version_id" in district_cols else "NULL::bigint"
            has_district_version = "source_version_id" in district_cols
            has_source_versions = bool(schema.get("source_versions"))
            # Una carga nueva puede convivir con instantáneas viejas. Escoger una
            # única versión por código evita duplicar distritos en el contrato API.
            if has_district_version and has_source_versions:
                await cur.execute(
                    """
                    SELECT DISTINCT ON (COALESCE(psd.group_code, ''), COALESCE(psd.special_code, ''))
                           psd.group_code, psd.special_code, psd.source_version_id
                    FROM public.parcel_special_districts psd
                    LEFT JOIN public.source_versions sv ON sv.id = psd.source_version_id
                    WHERE psd.parcel_id = %s
                      AND (sv.id IS NULL OR sv.status IN ('active', 'ingested'))
                    ORDER BY COALESCE(psd.group_code, ''), COALESCE(psd.special_code, ''),
                             (sv.status = 'active') DESC,
                             COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                             psd.source_version_id DESC,
                             psd.id DESC
                    """,
                    (parcel_id,),
                )
            else:
                order = " ORDER BY id" if "id" in district_cols else ""
                await cur.execute(
                    f"SELECT group_code, special_code, {district_version_expr} AS source_version_id "
                    f"FROM public.parcel_special_districts WHERE parcel_id = %s{order}",
                    (parcel_id,),
                )
            result["special_districts"] = [
                {"group_code": district[0], "special_code": district[1], "source_version_id": district[2]}
                for district in await cur.fetchall()
            ]
        return result

    async def _find_land_use(self, cur: Any, schema: dict[str, set[str]], parcel_id: int) -> list[dict[str, Any]]:
        cols = schema.get("land_use_observations", set())
        if not {"parcel_id"} <= cols:
            return []
        selected = ["id" if "id" in cols else "NULL::bigint AS id"]
        for col in ("source_record_id", "tipo1", "tipo2", "estado", "pisos", "obs", "anio", "source_version_id"):
            selected.append(col if col in cols else f"NULL AS {col}")
        order = " ORDER BY anio DESC NULLS LAST, id DESC" if {"anio", "id"} <= cols else (" ORDER BY id DESC" if "id" in cols else "")
        limit = max(1, min(int(settings.territory_land_use_limit), 100))
        await cur.execute(
            f"SELECT {', '.join(selected)} FROM public.land_use_observations WHERE parcel_id = %s{order} LIMIT %s",
            (parcel_id, limit),
        )
        names = ("id", "source_record_id", "tipo1", "tipo2", "estado", "pisos", "obs", "anio", "source_version_id")
        return [dict(zip(names, row, strict=True)) for row in await cur.fetchall()]
