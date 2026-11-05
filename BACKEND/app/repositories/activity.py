"""Resolución determinista de actividades por nombre/código y alias catalogados.

No usa embeddings ni similitud difusa. Si el texto coincide con más de una
actividad al nivel de coincidencia elegido, devuelve ambigüedad explícita.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.core.database import connection


def normalize_activity(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def normalize_activity_search(value: str) -> str:
    """Normalización léxica conservadora para autocomplete, no para resolver rubros.

    Iguala algunas flexiones de género/terminación frecuentes (p. ej. gastronomía /
    gastronómico) para sugerir candidatos. La resolución de una actividad sigue
    exigiendo nombre/alias exacto o activity_code explícito.
    """
    suffixes = ("icos", "icas", "ico", "ica", "ias", "ia")
    tokens = normalize_activity(value).split()
    normalized: list[str] = []
    for token in tokens:
        stem = token
        for suffix in suffixes:
            if len(token) > len(suffix) + 3 and token.endswith(suffix):
                stem = token[:-len(suffix)]
                break
        normalized.append(stem)
    return " ".join(normalized)


class ActivityRepository:
    """Catálogo en memoria por request; los datos canónicos permanecen en PostgreSQL."""

    async def _catalog(self) -> list[dict[str, Any]]:
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    a.id, a.code, a.name, a.category, a.mapping_status,
                    a.source_version_id AS activity_source_version_id,
                    aa.alias, aa.normalized_alias, aa.status AS alias_status,
                    aa.source_version_id AS alias_source_version_id
                FROM public.activities a
                JOIN public.source_versions activity_sv ON activity_sv.id = a.source_version_id
                  AND activity_sv.status IN ('active', 'ingested')
                LEFT JOIN public.activity_aliases aa ON aa.activity_id = a.id
                  AND (aa.status <> 'deprecated' OR aa.status IS NULL)
                  AND (
                      aa.source_version_id IS NULL
                      OR EXISTS (
                          SELECT 1 FROM public.source_versions alias_sv
                          WHERE alias_sv.id = aa.source_version_id
                            AND alias_sv.status IN ('active', 'ingested')
                      )
                  )
                WHERE a.mapping_status <> 'deprecated'
                ORDER BY a.code, aa.status = 'official' DESC NULLS LAST, aa.alias
                """
            )
            rows = await cur.fetchall()

        catalog: list[dict[str, Any]] = []
        for row in rows:
            base = {
                "id": int(row[0]),
                "code": str(row[1]),
                "name": str(row[2]),
                "category": row[3],
                "mapping_status": row[4],
                "source_version_id": row[5],
                "alias_source_version_id": row[9],
            }
            # Siempre se reconoce el nombre canónico. Los alias adicionales son
            # alternativas indexadas explícitamente, no una inferencia semántica.
            catalog.append({**base, "matched_alias": base["name"], "normalized_match": normalize_activity(base["name"]), "match_kind": "canonical"})
            if row[6]:
                normalized = str(row[7] or normalize_activity(str(row[6])))
                catalog.append({**base, "matched_alias": str(row[6]), "normalized_match": normalized, "match_kind": row[8] or "provisional"})
        return catalog

    @staticmethod
    def _dedupe_by_activity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        distinct: dict[int, dict[str, Any]] = {}
        for item in rows:
            activity_id = int(item["id"])
            previous = distinct.get(activity_id)
            if previous is None or (
                item.get("match_kind") == "official" and previous.get("match_kind") != "official"
            ):
                distinct[activity_id] = item
        return list(distinct.values())

    async def search_catalog(
        self, query: str | None = None, *, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Búsqueda deterministicable para autocomplete del Frontend, sin embeddings/IA."""
        q = normalize_activity(query or "")
        q_search = normalize_activity_search(query or "")
        rows = await self._catalog()
        # Agrupar por actividad para exponer nombres oficiales una sola vez, con sus alias explícitos.
        grouped: dict[int, dict[str, Any]] = {}
        alias_normalized: dict[int, set[str]] = {}
        for row in rows:
            activity_id = int(row["id"])
            item = grouped.setdefault(activity_id, {
                "id": activity_id, "code": row["code"], "name": row["name"],
                "category": row.get("category"), "mapping_status": row.get("mapping_status"),
                "source_version_id": row.get("source_version_id"), "aliases": [],
            })
            alias = row.get("matched_alias")
            if alias and normalize_activity(str(alias)) != normalize_activity(str(item["name"])):
                item["aliases"].append(str(alias))
            alias_normalized.setdefault(activity_id, set()).add(normalize_activity(str(alias or "")))

        candidates: list[tuple[int, str, dict[str, Any]]] = []
        for activity_id, item in grouped.items():
            name_norm = normalize_activity(item["name"])
            name_search = normalize_activity_search(item["name"])
            code_norm = normalize_activity(item["code"])
            aliases = alias_normalized.get(activity_id, set())
            aliases_search = {normalize_activity_search(alias) for alias in aliases}
            if not q:
                rank = 4
            elif q == code_norm or q == name_norm or q in aliases:
                rank = 0
            elif code_norm.startswith(q) or name_norm.startswith(q):
                rank = 1
            elif any(alias.startswith(q) for alias in aliases):
                rank = 2
            elif q in code_norm or q in name_norm or any(q in alias for alias in aliases):
                rank = 3
            elif q_search and (q_search in name_search or any(q_search in alias for alias in aliases_search)):
                rank = 3
            else:
                continue
            item["aliases"] = sorted(set(item["aliases"]), key=lambda value: normalize_activity(value))
            candidates.append((rank, str(item["code"]), item))

        candidates.sort(key=lambda row: (row[0], row[1], normalize_activity(row[2]["name"])))
        total = len(candidates)
        items = [item for _, _, item in candidates[offset:offset + limit]]
        return {
            "items": items, "total": total, "limit": limit, "offset": offset,
            "search": query or None, "search_method": "catalog_exact_prefix_substring_conservative_morphology",
            "execution_mode": "deterministic", "ai_used": False,
        }

    async def resolve_detailed(self, value: str) -> dict[str, Any]:
        """Resuelve una actividad ingresada como texto exacto o devuelve candidatos."""
        normalized = normalize_activity(value)
        if not normalized:
            return {"status": "not_found", "activity": None, "candidates": []}
        catalog = await self._catalog()
        matches = [item for item in catalog if item["normalized_match"] == normalized]
        matches = self._dedupe_by_activity(matches)
        matches.sort(key=lambda item: (item.get("match_kind") == "official", item["name"]), reverse=True)
        if len(matches) == 1:
            item = matches[0]
            return {"status": "resolved", "activity": self._public(item), "candidates": []}
        if len(matches) > 1:
            return {"status": "ambiguous", "activity": None, "candidates": [self._public(item) for item in matches]}
        return {"status": "not_found", "activity": None, "candidates": []}

    async def resolve_from_text(self, value: str) -> dict[str, Any]:
        """Encuentra nombres/alias dentro de una consulta, con coincidencia por tokens.

        Se selecciona la coincidencia textual más larga. Los empates entre rubros
        distintos se devuelven para confirmación en lugar de elegir arbitrariamente.
        """
        normalized_query = normalize_activity(value)
        if not normalized_query:
            return {"status": "not_found", "activity": None, "candidates": []}
        padded = f" {normalized_query} "
        catalog = await self._catalog()
        matches = [
            item for item in catalog
            if item["normalized_match"] and f" {item['normalized_match']} " in padded
        ]
        if not matches:
            return {"status": "not_found", "activity": None, "candidates": []}
        longest = max(len(item["normalized_match"]) for item in matches)
        matches = [item for item in matches if len(item["normalized_match"]) == longest]
        matches = self._dedupe_by_activity(matches)
        matches.sort(key=lambda item: (item["code"], item["name"]))
        if len(matches) == 1:
            return {"status": "resolved", "activity": self._public(matches[0]), "candidates": []}
        return {"status": "ambiguous", "activity": None, "candidates": [self._public(item) for item in matches]}


    async def resolve_by_code(self, code: str) -> dict[str, Any] | None:
        """Resuelve exclusivamente por código de catálogo, útil para confirmar opciones."""
        value = code.strip()
        if not value:
            return None
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT a.id, a.code, a.name, a.category, a.mapping_status, a.source_version_id
                FROM public.activities a
                JOIN public.source_versions sv ON sv.id = a.source_version_id
                  AND sv.status IN ('active', 'ingested')
                WHERE a.code = %s AND a.mapping_status <> 'deprecated'
                LIMIT 2
                """,
                (value,),
            )
            rows = await cur.fetchall()
        if len(rows) != 1:
            return None
        row = rows[0]
        return {
            "id": row[0], "code": row[1], "name": row[2], "category": row[3],
            "mapping_status": row[4], "source_version_id": row[5],
            "alias_source_version_id": None, "matched_alias": row[2],
            "match_kind": "code",
        }

    async def resolve(self, value: str) -> dict[str, Any] | None:
        """Compatibilidad con consumidores existentes: solo devuelve resolución única."""
        result = await self.resolve_detailed(value)
        return result["activity"] if result["status"] == "resolved" else None

    @staticmethod
    def _public(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "code": item["code"],
            "name": item["name"],
            "category": item.get("category"),
            "mapping_status": item.get("mapping_status"),
            "source_version_id": item.get("source_version_id"),
            "alias_source_version_id": item.get("alias_source_version_id"),
            "matched_alias": item.get("matched_alias"),
            "match_kind": item.get("match_kind"),
        }
