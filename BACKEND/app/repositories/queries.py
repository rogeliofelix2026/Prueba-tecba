"""Persistencia mínima de consultas y su evidencia estructurada."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from psycopg.types.json import Jsonb

from app.core.database import connection


class QueryRepository:
    async def start(
        self,
        request_id: uuid.UUID,
        question: str,
        activity_input: str,
        address: str | None,
        chat_model_id: int | None,
        embedding_model_id: int | None,
        request_payload: dict[str, Any] | None = None,
        execution_mode: str = "legacy",
    ) -> uuid.UUID:
        query_id = uuid.uuid4()
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO query_runs (
                    id,
                    request_id,
                    question,
                    activity_input,
                    address_input,
                    chat_model_id,
                    embedding_model_id,
                    request_payload,
                    execution_mode,
                    status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'started')
                """,
                (
                    query_id,
                    request_id,
                    question,
                    activity_input,
                    address,
                    chat_model_id,
                    embedding_model_id,
                    Jsonb(jsonable_encoder(request_payload or {})),
                    execution_mode,
                ),
            )
        return query_id

    async def update_context(
        self,
        query_id: uuid.UUID,
        activity_id: int | None,
        normalized_address: str | None,
        street_code: int | None,
        latitude: float | None,
        longitude: float | None,
        surface_m2: float | None,
        street_width_m: float | None,
        frontage_m: float | None,
        parcel_id: int | None,
    ) -> None:
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE query_runs
                SET activity_id = %s,
                    normalized_address = %s,
                    street_code = %s,
                    latitude = %s,
                    longitude = %s,
                    surface_m2 = %s,
                    street_width_m = %s,
                    frontage_m = %s,
                    parcel_id = %s
                WHERE id = %s
                """,
                (
                    activity_id,
                    normalized_address,
                    street_code,
                    latitude,
                    longitude,
                    surface_m2,
                    street_width_m,
                    frontage_m,
                    parcel_id,
                    query_id,
                ),
            )

    async def add_evidence(self, query_id: uuid.UUID, evidence: list[dict[str, Any]]) -> None:
        rag_items = [item for item in evidence if item.get("document_chunk_id") is not None]
        if not rag_items:
            return
        async with connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO query_evidence (
                    query_run_id,
                    evidence_type,
                    document_chunk_id,
                    source_version_id,
                    score
                ) VALUES (%s, 'rag', %s, %s, %s)
                """,
                [
                    (
                        query_id,
                        item.get("document_chunk_id"),
                        item.get("source_version_id"),
                        item.get("score"),
                    )
                    for item in rag_items
                ],
            )

    async def add_activity_rule_evidence(
        self,
        query_id: uuid.UUID,
        activity_rule_ids: list[int],
    ) -> None:
        ids = sorted({int(value) for value in activity_rule_ids})
        if not ids:
            return
        async with connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO query_evidence (
                    query_run_id,
                    evidence_type,
                    activity_use_rule_id
                ) VALUES (%s, 'activity_rule', %s)
                """,
                [(query_id, rule_id) for rule_id in ids],
            )

    async def add_urban_rule_evidence(
        self,
        query_id: uuid.UUID,
        urban_rule_id: int | None,
    ) -> None:
        if urban_rule_id is None:
            return
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO query_evidence (
                    query_run_id,
                    evidence_type,
                    urban_parcel_rule_id
                ) VALUES (%s, 'urban_parcel_rule', %s)
                """,
                (query_id, urban_rule_id),
            )

    async def add_source_evidence(
        self,
        query_id: uuid.UUID,
        source_version_ids: set[int],
    ) -> None:
        ids = sorted(value for value in source_version_ids if value is not None)
        if not ids:
            return
        async with connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO query_evidence (
                    query_run_id,
                    evidence_type,
                    source_version_id
                ) VALUES (%s, 'structured_source', %s)
                """,
                [(query_id, source_version_id) for source_version_id in ids],
            )

    async def complete(
        self,
        query_id: uuid.UUID,
        answer: str | None,
        partial: bool = False,
        response_json: dict[str, Any] | None = None,
        execution_mode: str | None = None,
    ) -> None:
        status = "partial" if partial else "completed"
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE query_runs
                SET status = %s,
                    response_text = %s,
                    response_json = COALESCE(%s, response_json),
                    execution_mode = COALESCE(%s, execution_mode),
                    completed_at = NOW()
                WHERE id = %s
                """,
                (status, answer, Jsonb(jsonable_encoder(response_json)) if response_json is not None else None, execution_mode, query_id),
            )

    async def fail(
        self,
        query_id: uuid.UUID,
        error_code: str,
        message: str | None = None,
    ) -> None:
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE query_runs
                SET status = 'failed',
                    error_code = %s,
                    error_message = %s,
                    completed_at = NOW()
                WHERE id = %s
                """,
                (error_code, message or error_code, query_id),
            )


    async def record_territory_result(
        self,
        *,
        query_id: uuid.UUID,
        request_id: uuid.UUID,
        question: str,
        activity_input: str | None,
        activity_id: int | None,
        address_input: str | None,
        normalized_address: str | None,
        street_code: int | None,
        latitude: float | None,
        longitude: float | None,
        surface_m2: float | None,
        street_width_m: float | None,
        frontage_m: float | None,
        parcel_id: int | None,
        input_payload: dict[str, Any],
        response_payload: dict[str, Any],
        source_version_ids: set[int],
        activity_use_rule_ids: list[int],
        urban_parcel_rule_id: int | None,
        procedure_rule_ids: list[int],
    ) -> dict[str, Any]:
        """Guarda la trazabilidad con compatibilidad para esquemas antes/después de v0.3.1.

        El registro básico no depende de que ya estén aplicadas las columnas JSON
        nuevas. Cuando existen, guarda también payloads estructurados y evidencia;
        si faltan, conserva el resultado base y lo informa como auditoría parcial.
        """
        db_status = "completed" if response_payload.get("status") == "resolved" else "partial"
        now = datetime.now(timezone.utc)
        encoded_input = jsonable_encoder(input_payload)
        encoded_response = jsonable_encoder(response_payload)

        async with connection() as conn:
            # Detectar capacidades sin asumir que la migración de auditoría más nueva
            # ya se aplicó en Supabase. Los nombres usados para generar SQL provienen
            # de una lista local cerrada y se intersectan con information_schema.
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name IN ('query_runs', 'query_evidence')
                    """
                )
                schema: dict[str, set[str]] = {}
                for table, column in await cur.fetchall():
                    schema.setdefault(str(table), set()).add(str(column))

            run_cols = schema.get("query_runs", set())
            required = {"id", "request_id", "question", "status"}
            if not required <= run_cols:
                return {
                    "status": "unavailable",
                    "warnings": ["QUERY_AUDIT_TABLE_OR_REQUIRED_COLUMNS_UNAVAILABLE"],
                }

            row_values: dict[str, Any] = {
                "id": query_id,
                "request_id": request_id,
                "question": question[:4000],
                "activity_input": activity_input,
                "activity_id": activity_id,
                "address_input": address_input,
                "normalized_address": normalized_address,
                "street_code": street_code,
                "latitude": latitude,
                "longitude": longitude,
                "surface_m2": surface_m2,
                "street_width_m": street_width_m,
                "frontage_m": frontage_m,
                "parcel_id": parcel_id,
                "request_payload": Jsonb(encoded_input),
                "response_json": Jsonb(encoded_response),
                "execution_mode": "deterministic",
                "status": db_status,
                "response_text": response_payload.get("next_action") or response_payload.get("status"),
                "started_at": now,
                "completed_at": now,
            }
            allowed_run_cols = (
                "id", "request_id", "question", "activity_input", "activity_id", "address_input",
                "normalized_address", "street_code", "latitude", "longitude", "surface_m2",
                "street_width_m", "frontage_m", "parcel_id", "request_payload", "response_json",
                "execution_mode", "status", "response_text", "started_at", "completed_at",
            )
            run_insert_cols = [column for column in allowed_run_cols if column in run_cols]
            run_sql = (
                "INSERT INTO public.query_runs ("
                + ", ".join(f'"{column}"' for column in run_insert_cols)
                + ") VALUES ("
                + ", ".join(["%s"] * len(run_insert_cols))
                + ")"
            )
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute(run_sql, tuple(row_values[column] for column in run_insert_cols))

            # La evidencia se confirma en una transacción separada. Un esquema viejo
            # o una FK de evidencia desactualizada no borra el query_run básico.
            evidence_cols = schema.get("query_evidence", set())
            evidence_warning: str | None = None
            evidence_count = 0
            try:
                if {"query_run_id", "evidence_type"} <= evidence_cols:
                    events: list[dict[str, Any]] = []
                    events.extend(
                        {
                            "query_run_id": query_id,
                            "evidence_type": "structured_source",
                            "reference_key": f"source_version:{int(source_id)}",
                            "source_version_id": int(source_id),
                        }
                        for source_id in sorted(source_version_ids)
                    )
                    events.extend(
                        {
                            "query_run_id": query_id,
                            "evidence_type": "activity_rule",
                            "reference_key": f"activity_use_rule:{int(rule_id)}",
                            "activity_use_rule_id": int(rule_id),
                        }
                        for rule_id in sorted({int(value) for value in activity_use_rule_ids})
                    )
                    if urban_parcel_rule_id is not None:
                        events.append({
                            "query_run_id": query_id,
                            "evidence_type": "urban_parcel_rule",
                            "reference_key": f"urban_parcel_rule:{int(urban_parcel_rule_id)}",
                            "urban_parcel_rule_id": int(urban_parcel_rule_id),
                        })
                    events.extend(
                        {
                            "query_run_id": query_id,
                            "evidence_type": "procedure_rule",
                            "reference_key": f"procedure_rule:{int(rule_id)}",
                            "procedure_rule_id": int(rule_id),
                        }
                        for rule_id in sorted({int(value) for value in procedure_rule_ids})
                    )
                    evidence_fields = (
                        "query_run_id", "evidence_type", "reference_key", "document_chunk_id", "activity_use_rule_id",
                        "urban_parcel_rule_id", "procedure_rule_id", "source_version_id",
                    )
                    # No insertar evidencia vacía: debe conservar al menos una FK que
                    # indique qué fuente/regla se está registrando.
                    insertable = []
                    for event in events:
                        filtered = {key: value for key, value in event.items() if key in evidence_cols and key in evidence_fields}
                        has_reference = any(
                            filtered.get(key) is not None
                            for key in ("document_chunk_id", "activity_use_rule_id", "urban_parcel_rule_id", "procedure_rule_id", "source_version_id")
                        )
                        if has_reference:
                            insertable.append(filtered)
                    if insertable:
                        evidence_insert_cols = [
                            key for key in evidence_fields
                            if key in evidence_cols and any(key in event for event in insertable)
                        ]
                        evidence_sql = (
                            "INSERT INTO public.query_evidence ("
                            + ", ".join(f'"{column}"' for column in evidence_insert_cols)
                            + ") VALUES ("
                            + ", ".join(["%s"] * len(evidence_insert_cols))
                            + ")"
                        )
                        evidence_rows = [
                            tuple(event.get(column) for column in evidence_insert_cols)
                            for event in insertable
                        ]
                        async with conn.transaction():
                            async with conn.cursor() as cur:
                                await cur.executemany(evidence_sql, evidence_rows)
                        evidence_count = len(evidence_rows)
                elif source_version_ids or activity_use_rule_ids or urban_parcel_rule_id is not None or procedure_rule_ids:
                    evidence_warning = "QUERY_EVIDENCE_SCHEMA_UNAVAILABLE"
            except Exception:
                evidence_warning = "QUERY_EVIDENCE_PERSISTENCE_FAILED"

            modern_fields = {"request_payload", "response_json", "execution_mode"} <= run_cols
            full_evidence_schema = {"query_run_id", "evidence_type", "source_version_id", "activity_use_rule_id", "urban_parcel_rule_id", "procedure_rule_id"} <= evidence_cols
            final_status = "stored" if modern_fields and full_evidence_schema and not evidence_warning else "stored_partial"
            warnings = []
            if not modern_fields:
                warnings.append("QUERY_AUDIT_SCHEMA_LEGACY")
            if evidence_warning:
                warnings.append(evidence_warning)

            # Sincronizar el trace que queda serializado en response_json con el
            # resultado final de persistencia (el primer INSERT se hace antes de
            # poder conocer si la escritura de evidencias fue exitosa).
            if "response_json" in run_cols:
                persisted_response = dict(response_payload)
                persisted_trace = dict(persisted_response.get("trace") or {})
                persisted_trace.update({
                    "query_run_id": str(query_id),
                    "persistence_status": final_status,
                    "audit_schema": "structured" if modern_fields else "legacy_compatible",
                    "evidence_rows": evidence_count,
                })
                persisted_response["trace"] = persisted_trace
                persisted_response["warnings"] = list(dict.fromkeys(
                    [*(persisted_response.get("warnings") or []), *warnings]
                ))
                try:
                    async with conn.transaction():
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "UPDATE public.query_runs SET response_json = %s WHERE id = %s",
                                (Jsonb(jsonable_encoder(persisted_response)), query_id),
                            )
                except Exception:
                    warnings.append("QUERY_AUDIT_RESPONSE_TRACE_UPDATE_FAILED")
                    final_status = "stored_partial"

            return {
                "status": final_status,
                "warnings": warnings,
                "evidence_rows": evidence_count,
                "audit_schema": "structured" if modern_fields else "legacy_compatible",
            }
