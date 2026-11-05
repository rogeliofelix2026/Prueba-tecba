"""Prueba de aceptación extremo a extremo: API determinista + persistencia real.

No modifica el esquema. Ejecuta una consulta real contra la API (que agrega query_runs/evidencias)
y verifica que el resultado corresponda a una fila persistida en la misma base DATABASE_URL.
Por defecto exige el flujo completo; si falta dato normativo/territorial, termina con diagnóstico.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx
import psycopg

from app.core.config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SGI_API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--activity", default=os.getenv("SGI_SMOKE_ACTIVITY", "Alimentación en general y gastronomía"))
    parser.add_argument("--address", default=os.getenv("SGI_SMOKE_ADDRESS", "Corrientes 2500"))
    parser.add_argument("--surface-m2", type=float, default=float(os.getenv("SGI_SMOKE_SURFACE_M2", "80")))
    parser.add_argument("--timeout", type=float, default=35.0)
    parser.add_argument("--allow-partial", action="store_true", help="Verifica contrato y persistencia aunque falten datos del flujo")
    return parser.parse_args()


def fail(message: str, payload: Any | None = None) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    if payload is not None:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str), file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()
    try:
        database_url = settings.require_database_url()
    except Exception as exc:
        return fail(f"DATABASE_URL inválida/no configurada: {exc}")

    request_payload = {
        "activity": args.activity,
        "address": args.address,
        "surface_m2": args.surface_m2,
        "include_geometry": False,
    }
    try:
        with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
            response = client.post(f"{args.base_url.rstrip('/')}/api/v1/territory", json=request_payload)
    except httpx.HTTPError as exc:
        return fail(f"No se pudo llamar a la API en {args.base_url}: {exc}")

    try:
        payload = response.json()
    except ValueError:
        return fail(f"La API devolvió HTTP {response.status_code} y una respuesta no JSON: {response.text[:600]}")
    if response.status_code != 200:
        return fail(f"La API devolvió HTTP {response.status_code}", payload)

    required_top_level = {
        "request_id", "generated_at", "query", "execution", "activity", "location",
        "territory", "compatibility", "procedure_type_mapping", "procedures", "sources", "warnings", "trace",
    }
    missing_keys = sorted(required_top_level - set(payload))
    if missing_keys:
        return fail(f"Respuesta sin claves contractuales: {missing_keys}", payload)
    execution = payload.get("execution") or {}
    if execution.get("mode") != "deterministic" or execution.get("ai_used") is not False:
        return fail("El endpoint principal no acredita decisiones determinísticas", execution)
    input_stage = (execution.get("ai_stages") or {}).get("input_interpreter") or {}
    if input_stage.get("used") is True:
        return fail("El smoke test exige input determinístico; desactivá AI_INPUT_INTERPRETER_ENABLED", input_stage)
    trace = payload.get("trace") or {}
    if trace.get("persistence_status") != "stored" or not trace.get("query_run_id"):
        return fail("La API no confirma una persistencia real de query_runs", trace)

    status = payload.get("status")
    if status != "resolved" and not args.allow_partial:
        return fail(
            "El flujo no alcanzó estado 'resolved'. Revisar las advertencias y el bloque faltante; "
            "no es correcto aprobar el contrato con un resultado parcial.",
            {"status": status, "warnings": payload.get("warnings"), "activity": payload.get("activity"),
             "location": payload.get("location"), "territory": payload.get("territory"),
             "compatibility": payload.get("compatibility"), "procedure_type_mapping": payload.get("procedure_type_mapping"),
             "procedures": payload.get("procedures")},
        )

    if payload.get("location") is None:
        return fail("No se recuperó la localización de USIG", payload.get("location"))

    try:
        with psycopg.connect(database_url, connect_timeout=8, options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, request_id, status, execution_mode, request_payload, response_json,
                              activity_id, parcel_id
                       FROM public.query_runs WHERE id = %s AND request_id = %s""",
                    (trace["query_run_id"], payload["request_id"]),
                )
                row = cur.fetchone()
                if row is None:
                    return fail("La API devolvió query_run_id, pero no existe la fila en esta DATABASE_URL")
                run_id, request_id, db_status, mode, saved_input, saved_output, activity_id, parcel_id = row
                if mode != "deterministic":
                    return fail(f"execution_mode esperado=deterministic, DB={mode}")
                if not isinstance(saved_input, dict) or saved_input.get("activity_input") != args.activity:
                    return fail("request_payload no conserva la actividad explícita", saved_input)
                if not isinstance(saved_output, dict) or saved_output.get("request_id") != payload.get("request_id"):
                    return fail("response_json no conserva la respuesta estructurada completa")
                cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE evidence_type='structured_source') FROM public.query_evidence WHERE query_run_id=%s", (run_id,))
                evidence_count, source_evidence_count = cur.fetchone()
                if db_status not in {"completed", "partial"}:
                    return fail(f"Estado DB inesperado después de terminar: {db_status}")
                if not args.allow_partial and (not activity_id or not parcel_id):
                    return fail(f"Persistencia incompleta: activity_id={activity_id}, parcel_id={parcel_id}")
                if not args.allow_partial and source_evidence_count == 0:
                    return fail("El resultado se guardó pero no tiene evidencia de origen", {"evidence_count": evidence_count})
    except psycopg.Error as exc:
        return fail(f"No se pudo verificar la persistencia en PostgreSQL: {type(exc).__name__}: {exc}")

    summary = {
        "result": "PASS",
        "status": status,
        "request_id": payload["request_id"],
        "query_run_id": str(run_id),
        "activity": (payload.get("activity") or {}).get("name"),
        "normalized_address": (payload.get("location") or {}).get("address_normalized"),
        "smp": ((payload.get("territory") or {}).get("parcel") or {}).get("smp"),
        "barrio": (((payload.get("territory") or {}).get("administrative") or {}).get("barrio") or {}).get("name"),
        "comuna": (((payload.get("territory") or {}).get("administrative") or {}).get("comuna") or {}).get("name"),
        "mixturas": ((payload.get("territory") or {}).get("urbanism") or {}).get("mixturas"),
        "compatibility_status": (payload.get("compatibility") or {}).get("status"),
        "procedure_mapping_status": (payload.get("procedure_type_mapping") or {}).get("status"),
        "procedure_details_status": (payload.get("procedures") or {}).get("detail_status"),
        "sources": len(payload.get("sources") or []),
        "evidence_rows": evidence_count,
        "source_evidence_rows": source_evidence_count,
        "warnings": payload.get("warnings") or [],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
