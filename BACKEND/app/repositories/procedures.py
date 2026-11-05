"""Recupera detalles de trámites sin asumir que todas sus tablas estén cargadas."""
from __future__ import annotations

from typing import Any

from app.core.database import connection
from app.core.procedure_codes import VARIANT_CODE_SQL_CASE


_CORE_COLUMNS = {
    # The Anexo II mapping can resolve the procedure type without manual links.
    # activity_procedures is therefore optional, not a prerequisite for this repo.
    "procedures": {"id", "code", "name", "source_version_id"},
    "source_versions": {"id", "status", "effective_from", "published_at"},
}
_ASSOCIATION_COLUMNS = {"id", "activity_id", "procedure_id", "source_version_id"}
_DETAIL_COLUMNS = {
    "procedure_variants": {"id", "procedure_id", "code", "name", "description", "conditions", "immediate_start_allowed", "prior_inspection_required", "validity_years", "source_version_id"},
    "procedure_requirements": {"id", "procedure_id", "requirement_code", "title", "description", "conditional", "conditions", "source_version_id"},
    "procedure_documents": {"id", "procedure_id", "document_code", "title", "description", "conditional", "conditions", "source_version_id"},
    "procedure_steps": {"id", "procedure_id", "step_order", "title", "description", "source_version_id"},
    "procedure_rules": {"id", "activity_procedure_id", "rule_type", "priority", "min_surface_m2", "max_surface_m2", "conditions", "rationale", "active", "source_version_id"},
}


class ProcedureRepository:
    async def for_activity(self, activity_id: int) -> list[dict[str, Any]]:
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s)
                """,
                (["activity_procedures", *_CORE_COLUMNS.keys(), *_DETAIL_COLUMNS.keys(), "activity_tramite_mappings"],),
            )
            schema: dict[str, set[str]] = {}
            for table_name, column_name in await cur.fetchall():
                schema.setdefault(str(table_name), set()).add(str(column_name))

            # Las tablas de detalle son opcionales para el vertical slice. Si las
            # tablas base no están disponibles, se informa “no cargado” al servicio
            # en vez de emitir SQL contra relaciones/columnas inexistentes.
            for table, required in _CORE_COLUMNS.items():
                if not required <= schema.get(table, set()):
                    return []

            procedures: list[dict[str, Any]] = []
            association_cols = schema.get("activity_procedures", set())
            if _ASSOCIATION_COLUMNS <= association_cols:
                priority_expr = "ap.priority" if "priority" in association_cols else "100::integer"
                description_expr = "p.description" if "description" in schema["procedures"] else "NULL::text"
                await cur.execute(
                    f"""
                    WITH ranked AS (
                        SELECT
                            ap.id AS activity_procedure_id,
                            ap.activity_id,
                            ap.procedure_id,
                            ap.source_version_id AS activity_procedure_source_version_id,
                            {priority_expr} AS priority,
                            p.code,
                            p.name,
                            {description_expr} AS description,
                            p.source_version_id AS procedure_source_version_id,
                            ROW_NUMBER() OVER (
                                PARTITION BY ap.activity_id, ap.procedure_id
                                ORDER BY
                                    (sv.status = 'active') DESC,
                                    COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                                    sv.id DESC
                            ) AS rn
                        FROM public.activity_procedures ap
                        JOIN public.source_versions sv ON sv.id = ap.source_version_id
                        JOIN public.procedures p ON p.id = ap.procedure_id
                        WHERE ap.activity_id = %s
                          AND sv.status IN ('active', 'ingested')
                    )
                    SELECT activity_procedure_id, procedure_id, code, name, description,
                           priority, activity_procedure_source_version_id,
                           procedure_source_version_id
                    FROM ranked
                    WHERE rn = 1
                    ORDER BY priority, name
                    """,
                    (activity_id,),
                )
                procedures = [
                    {
                        "activity_procedure_id": row[0],
                        "id": row[1],
                        "code": row[2],
                        "name": row[3],
                        "description": row[4],
                        "priority": row[5],
                        "source_version_id": row[6],
                        "procedure_source_version_id": row[7],
                        "requisitos": [],
                        "documentos": [],
                        "pasos": [],
                        "reglas": [],
                        "variantes": [],
                        "selected_by_activity_mapping": False,
                    }
                    for row in await cur.fetchall()
                ]

            # Si no existen relaciones manuales actividad_procedures (situación del
            # piloto), resolver el detalle desde el mapeo explícito de Anexo II y las
            # variantes cuyo código coincide. Conditional conserva todas las opciones.
            mapping_columns = schema.get("activity_tramite_mappings", set())
            variant_columns = schema.get("procedure_variants", set())
            # La columna active existe en algunos despliegues, pero no en el esquema
            # real compartido por el equipo. La ausencia no debe deshabilitar los mapeos.
            variant_active_filter = "pv.active = TRUE" if "active" in variant_columns else "TRUE"
            mapping_required = {
                "activity_id", "source_version_id", "mapping_status",
                "procedure_type_code", "possible_procedure_type_codes",
            }
            if not procedures and mapping_required <= mapping_columns and _DETAIL_COLUMNS["procedure_variants"] <= variant_columns:
                description_expr = "p.description" if "description" in schema["procedures"] else "NULL::text"
                await cur.execute(
                    f"""
                    WITH selected_mapping AS (
                        SELECT atm.mapping_status, atm.procedure_type_code,
                               atm.possible_procedure_type_codes, atm.source_version_id,
                               ROW_NUMBER() OVER (
                                   ORDER BY (sv.status = 'active') DESC,
                                            COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                                            sv.id DESC
                               ) AS rn
                        FROM public.activity_tramite_mappings atm
                        JOIN public.source_versions sv ON sv.id = atm.source_version_id
                        WHERE atm.activity_id = %s
                          AND atm.mapping_status IN ('confirmed', 'conditional')
                          AND sv.status IN ('active', 'ingested')
                    ), candidate_codes AS (
                        SELECT m.mapping_status, m.procedure_type_code AS confirmed_procedure_type_code,
                               m.source_version_id AS mapping_source_version_id,
                               candidate.code AS candidate_procedure_type_code,
                               {VARIANT_CODE_SQL_CASE} AS variant_code
                        FROM selected_mapping m
                        CROSS JOIN LATERAL unnest(
                            CASE
                              WHEN m.mapping_status = 'confirmed' AND m.procedure_type_code IS NOT NULL
                                THEN ARRAY[m.procedure_type_code]::TEXT[]
                              WHEN m.mapping_status = 'conditional'
                                THEN COALESCE(m.possible_procedure_type_codes, ARRAY[]::TEXT[])
                              ELSE ARRAY[]::TEXT[]
                            END
                        ) AS candidate(code)
                        WHERE m.rn = 1
                    )
                    SELECT p.id, p.code, p.name, {description_expr} AS description,
                           100::integer AS priority, c.mapping_source_version_id,
                           p.source_version_id AS procedure_source_version_id,
                           pv.code, pv.name, pv.description, pv.conditions,
                           pv.immediate_start_allowed, pv.prior_inspection_required,
                           pv.validity_years, pv.source_version_id,
                           c.mapping_source_version_id, c.mapping_status, c.candidate_procedure_type_code
                    FROM candidate_codes c
                    JOIN public.procedure_variants pv ON pv.code = c.variant_code AND {variant_active_filter}
                    JOIN public.source_versions vsv ON vsv.id = pv.source_version_id
                      AND vsv.status IN ('active', 'ingested')
                    JOIN public.procedures p ON p.id = pv.procedure_id
                    JOIN public.source_versions psv ON psv.id = p.source_version_id
                      AND psv.status IN ('active', 'ingested')
                    ORDER BY p.name, pv.code
                    """,
                    (activity_id,),
                )
                by_procedure: dict[int, dict[str, Any]] = {}
                for row in await cur.fetchall():
                    procedure_id = int(row[0])
                    item = by_procedure.setdefault(procedure_id, {
                        "activity_procedure_id": None,
                        "id": procedure_id,
                        "code": row[1],
                        "name": row[2],
                        "description": row[3],
                        "priority": row[4],
                        "source_version_id": row[5],
                        "procedure_source_version_id": row[6],
                        "requisitos": [], "documentos": [], "pasos": [], "reglas": [],
                        "variantes": [],
                        "selected_by_activity_mapping": True,
                        "mapping_status": row[16],
                        "mapping_source_version_id": row[15],
                        "mapped_procedure_type_code": row[17],
                        "mapped_variant_codes": [],
                    })
                    item["mapped_variant_codes"].append(row[7])
                    item["variantes"].append({
                        "code": row[7], "name": row[8], "description": row[9],
                        "conditions": row[10] or {}, "immediate_start_allowed": row[11],
                        "prior_inspection_required": row[12], "validity_years": row[13],
                        "source_version_id": row[14],
                    })
                procedures = list(by_procedure.values())

            if not procedures:
                return []
            by_procedure_id = {item["id"]: item for item in procedures}

            missing_detail_tables = [
                table for table, required in _DETAIL_COLUMNS.items()
                if not required <= schema.get(table, set())
            ]
            for item in procedures:
                item["detail_schema_status"] = "partial" if missing_detail_tables else "available"
                item["detail_warnings"] = [f"{table.upper()}_SCHEMA_UNAVAILABLE" for table in missing_detail_tables]

            procedure_ids = [item["id"] for item in procedures]
            if "procedure_variants" not in missing_detail_tables:
                await cur.execute(
                    f"""
                    SELECT pv.procedure_id, pv.code, pv.name, pv.description, pv.conditions,
                           pv.immediate_start_allowed, pv.prior_inspection_required,
                           pv.validity_years, pv.source_version_id
                    FROM public.procedure_variants pv
                    JOIN public.source_versions sv ON sv.id = pv.source_version_id
                    WHERE pv.procedure_id = ANY(%s) AND {variant_active_filter}
                      AND sv.status IN ('active', 'ingested')
                    ORDER BY pv.procedure_id, pv.code
                    """,
                    (procedure_ids,),
                )
                variants = await cur.fetchall()
                for row in variants:
                    item = by_procedure_id.get(row[0])
                    if item is None:
                        continue
                    if item.get("selected_by_activity_mapping") and row[1] not in item.get("mapped_variant_codes", []):
                        continue
                    if any(value.get("code") == row[1] for value in item["variantes"]):
                        continue
                    item["variantes"].append({
                        "code": row[1], "name": row[2], "description": row[3],
                        "conditions": row[4] or {}, "immediate_start_allowed": row[5],
                        "prior_inspection_required": row[6], "validity_years": row[7],
                        "source_version_id": row[8],
                    })

            requirements: list[tuple] = []
            documents: list[tuple] = []
            steps: list[tuple] = []
            rules: list[tuple] = []

            if "procedure_requirements" not in missing_detail_tables:
                await cur.execute(
                    """
                    SELECT procedure_id, requirement_code, title, description,
                           conditional, conditions, source_version_id
                    FROM public.procedure_requirements
                    WHERE procedure_id = ANY(%s)
                    ORDER BY procedure_id, id
                    """,
                    (procedure_ids,),
                )
                requirements = await cur.fetchall()

            if "procedure_documents" not in missing_detail_tables:
                await cur.execute(
                    """
                    SELECT procedure_id, document_code, title, description,
                           conditional, conditions, source_version_id
                    FROM public.procedure_documents
                    WHERE procedure_id = ANY(%s)
                    ORDER BY procedure_id, id
                    """,
                    (procedure_ids,),
                )
                documents = await cur.fetchall()

            if "procedure_steps" not in missing_detail_tables:
                await cur.execute(
                    """
                    SELECT procedure_id, step_order, title, description, source_version_id
                    FROM public.procedure_steps
                    WHERE procedure_id = ANY(%s)
                    ORDER BY procedure_id, step_order
                    """,
                    (procedure_ids,),
                )
                steps = await cur.fetchall()

            if "procedure_rules" not in missing_detail_tables:
                await cur.execute(
                    """
                    SELECT ap.procedure_id, pr.id, pr.rule_type, pr.priority,
                           pr.min_surface_m2, pr.max_surface_m2, pr.conditions,
                           pr.rationale, pr.active, pr.source_version_id
                    FROM public.procedure_rules pr
                    JOIN public.activity_procedures ap ON ap.id = pr.activity_procedure_id
                    WHERE ap.procedure_id = ANY(%s) AND pr.active = TRUE
                    ORDER BY ap.procedure_id, pr.priority, pr.id
                    """,
                    (procedure_ids,),
                )
                rules = await cur.fetchall()

        by_id = by_procedure_id
        for row in requirements:
            by_id[row[0]]["requisitos"].append({
                "code": row[1], "title": row[2], "description": row[3],
                "conditional": row[4], "conditions": row[5] or {}, "source_version_id": row[6],
            })
        for row in documents:
            by_id[row[0]]["documentos"].append({
                "code": row[1], "title": row[2], "description": row[3],
                "conditional": row[4], "conditions": row[5] or {}, "source_version_id": row[6],
            })
        for row in steps:
            by_id[row[0]]["pasos"].append({
                "order": row[1], "title": row[2], "description": row[3], "source_version_id": row[4],
            })
        for row in rules:
            by_id[row[0]]["reglas"].append({
                "id": row[1], "rule_type": row[2], "priority": row[3],
                "min_surface_m2": row[4], "max_surface_m2": row[5],
                "conditions": row[6] or {}, "rationale": row[7],
                "active": row[8], "source_version_id": row[9],
            })
        return procedures
