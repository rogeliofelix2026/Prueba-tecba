"""Auditoría READ-ONLY del esquema SGI y sus capacidades reales.

No modifica datos ni intenta corregir el esquema automáticamente.
Detecta contratos compactos y legacy utilizados por el backend v0.3.0.
"""
from __future__ import annotations

import sys
from collections import defaultdict

import psycopg

from app.core.config import settings

CORE_TABLES = {
    "sources", "source_versions", "parcels", "barrios", "comunas",
    "urban_parcel_rules", "activities", "activity_aliases", "activity_use_rules",
    "geocoding_cache",
}
OPTIONAL_TABLES = {
    "parcel_geometries", "parcel_special_districts", "land_use_observations",
    "activity_tramite_mappings", "procedures", "activity_procedures",
    "procedure_rules", "procedure_requirements", "procedure_documents", "procedure_steps",
    "documents", "document_chunks", "query_runs", "query_evidence", "ai_models",
}
COUNTS = (
    "activities", "activity_aliases", "activity_use_rules", "parcels",
    "urban_parcel_rules", "parcel_special_districts", "land_use_observations",
    "activity_tramite_mappings", "procedures", "activity_procedures",
    "procedure_requirements", "procedure_documents", "procedure_steps", "document_chunks",
)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        database_url = settings.require_database_url()
        # La sesión completa es de solo lectura: una auditoría no debe mutar la BD.
        with psycopg.connect(database_url, options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_type='BASE TABLE'"
                )
                tables = {str(row[0]) for row in cur.fetchall()}
                missing_tables = sorted(CORE_TABLES - tables)
                if missing_tables:
                    errors.append(f"Faltan tablas base: {', '.join(missing_tables)}")

                cur.execute(
                    "SELECT table_name, column_name, data_type, udt_name "
                    "FROM information_schema.columns WHERE table_schema='public'"
                )
                columns: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
                for table, column, data_type, udt_name in cur.fetchall():
                    columns[str(table)][str(column)] = (str(data_type), str(udt_name))

                parcel_cols = set(columns.get("parcels", {}))
                required_parcel_cols = {"id", "smp", "source_version_id"}
                if not required_parcel_cols <= parcel_cols:
                    errors.append(
                        "public.parcels carece de columnas requeridas: "
                        + ", ".join(sorted(required_parcel_cols - parcel_cols))
                    )

                barrio_join = "barrio_id" in parcel_cols and "barrios" in tables
                barrio_text = "barrio" in parcel_cols
                if not barrio_join and not barrio_text:
                    errors.append("No hay relación de barrio: se esperaba parcels.barrio_id → barrios o parcels.barrio legado.")

                comuna_available = (
                    "comuna_id" in parcel_cols
                    or "comuna" in parcel_cols
                    or (barrio_join and "comuna_id" in columns.get("barrios", {}))
                )
                if not comuna_available:
                    warnings.append("No se detectó una relación de comuna; el API devolverá comuna=null.")

                rule_cols = set(columns.get("urban_parcel_rules", {}))
                if not {"parcel_id"} <= rule_cols:
                    errors.append("public.urban_parcel_rules debe relacionarse por parcel_id.")
                if "mixturas" not in rule_cols and not ({"uso_1", "uso_2", "uso_3"} & rule_cols):
                    errors.append("urban_parcel_rules no tiene mixturas ni columnas legacy uso_1/uso_2/uso_3.")
                if "source_version_id" not in rule_cols:
                    warnings.append("urban_parcel_rules no incluye source_version_id: se reduce la trazabilidad.")

                geometry = any(name in parcel_cols for name in ("geometry", "geom"))
                cache_cols = set(columns.get("parcel_geometries", {}))
                cache_geometry = any(name in cache_cols for name in ("geometry", "geom")) and bool({"parcel_id", "smp"} & cache_cols)
                if not geometry and not cache_geometry:
                    warnings.append("No hay geometría catastral utilizable; el flujo todavía puede resolver por SMP, pero el mapa no tendrá polígono ni fallback espacial.")
                else:
                    print(f"Geometría parcelaria: {'parcels' if geometry else 'parcel_geometries (caché)'}")

                mapping_cols = set(columns.get("activity_tramite_mappings", {}))
                mapping_required = {
                    "activity_id", "source_version_id", "activity_code_snapshot",
                    "catalog_activity_name_snapshot", "annex_ii_activity_name_verified",
                    "procedure_type_code", "procedure_type_label", "possible_procedure_type_codes",
                    "mapping_status", "mapping_method", "annex_ii_page", "source_annex_id",
                }
                if not mapping_cols:
                    warnings.append("Falta activity_tramite_mappings: el tipo de trámite aparecerá como no disponible.")
                elif not mapping_required <= mapping_cols:
                    warnings.append("activity_tramite_mappings tiene esquema incompleto: " + ", ".join(sorted(mapping_required - mapping_cols)))

                cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('postgis','vector','unaccent','pgcrypto')")
                extensions = {str(row[0]) for row in cur.fetchall()}
                if "postgis" not in extensions:
                    warnings.append("PostGIS no está habilitado: ST_Covers/mapa no estarán disponibles.")
                if "vector" not in extensions:
                    warnings.append("pgvector no está habilitado: la parte RAG/embeddings no estará disponible.")

                print("\nConteos de tablas disponibles:")
                for table in COUNTS:
                    if table not in tables:
                        print(f"  {table:32} — tabla ausente")
                        continue
                    cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
                    count = int(cur.fetchone()[0])
                    print(f"  {table:32} {count:>12,}")

    except Exception as exc:
        print(f"ERROR de auditoría de solo lectura: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print("\nResultado:")
    if errors:
        print("  INCOMPATIBLE para el flujo territorial:")
        for message in errors:
            print(f"  - {message}")
    else:
        print("  Contrato base territorial compatible.")
    if warnings:
        print("\nAdvertencias/capacidades parciales:")
        for message in warnings:
            print(f"  - {message}")
    print("\nModo READ-ONLY: no se aplicaron migraciones ni se modificaron filas.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
