"""Consulta del mapeo auditado actividad -> tipo de trámite (Anexo II)."""
from __future__ import annotations

from typing import Any

from app.core.database import connection


_REQUIRED_COLUMNS = {
    "activity_id", "source_version_id", "activity_code_snapshot",
    "catalog_activity_name_snapshot", "annex_ii_activity_name_verified",
    "procedure_type_code", "procedure_type_label",
    "possible_procedure_type_codes", "mapping_status", "mapping_method",
    "annex_ii_page", "observations", "source_annex_id",
}


class ActivityTramiteMappingRepository:
    async def for_activity(self, activity_id: int) -> dict[str, Any]:
        """Devuelve el mapeo vigente o un estado explícito si falta la migración/dato."""
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'activity_tramite_mappings'
                """
            )
            columns = {row[0] for row in await cur.fetchall()}
            if not columns:
                return {
                    "status": "schema_missing",
                    "procedure_type_code": None,
                    "procedure_type_label": None,
                    "possible_procedure_types": [],
                    "source_version_id": None,
                    "warnings": ["ACTIVITY_TRAMITE_MAPPING_MIGRATION_REQUIRED"],
                }
            missing = sorted(_REQUIRED_COLUMNS - columns)
            if missing:
                return {
                    "status": "schema_incompatible",
                    "procedure_type_code": None,
                    "procedure_type_label": None,
                    "possible_procedure_types": [],
                    "source_version_id": None,
                    "warnings": ["ACTIVITY_TRAMITE_MAPPING_SCHEMA_INCOMPATIBLE:" + ",".join(missing)],
                }
            await cur.execute(
                """
                WITH ranked AS (
                    SELECT atm.*,
                           sv.version_label,
                           sv.status AS source_status,
                           sv.published_at,
                           sv.effective_from,
                           ROW_NUMBER() OVER (
                               PARTITION BY atm.activity_id
                               ORDER BY (sv.status = 'active') DESC,
                                        COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                                        sv.id DESC, atm.id DESC
                           ) AS rn
                    FROM public.activity_tramite_mappings atm
                    JOIN public.source_versions sv ON sv.id = atm.source_version_id
                    WHERE atm.activity_id = %s
                      AND sv.status IN ('active', 'ingested')
                )
                SELECT id, activity_code_snapshot, catalog_activity_name_snapshot,
                       annex_ii_activity_name_verified, procedure_type_code,
                       procedure_type_label, possible_procedure_type_codes,
                       mapping_status, mapping_method, annex_ii_page, observations,
                       source_annex_id, source_version_id, version_label, source_status,
                       published_at, effective_from
                FROM ranked WHERE rn = 1
                """,
                (activity_id,),
            )
            row = await cur.fetchone()
        if row is None:
            return {
                "status": "not_found_in_anexo_ii",
                "procedure_type_code": None,
                "procedure_type_label": None,
                "possible_procedure_types": [],
                "source_version_id": None,
                "warnings": ["ACTIVITY_MAPPING_NOT_FOUND"],
            }
        status = str(row[7])
        warning_list = []
        if status != "confirmed":
            warning_list.append("ACTIVITY_TRAMITE_MAPPING_REQUIRES_REVIEW")
        return {
            "mapping_id": row[0],
            "activity_code": row[1],
            "catalog_activity_name": row[2],
            "annex_ii_activity_name": row[3],
            "procedure_type_code": row[4],
            "procedure_type_label": row[5],
            "possible_procedure_types": list(row[6] or []),
            "status": status,
            "method": row[8],
            "annex_ii_page": row[9],
            "observations": row[10],
            "source_annex_id": row[11],
            "source_version_id": row[12],
            "source_version": row[13],
            "source_status": row[14],
            "published_at": row[15].isoformat() if row[15] else None,
            "effective_from": row[16].isoformat() if row[16] else None,
            "warnings": warning_list,
        }
