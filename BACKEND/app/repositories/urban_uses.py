"""Acceso a las reglas normalizadas del Cuadro de Usos 3.3."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool


class UrbanUseRuleRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def for_activity(self, activity_id: int) -> dict[int, dict[str, Any]]:
        async with self._pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    aur.id,
                    aur.mixtura,
                    aur.raw_value,
                    aur.status,
                    aur.max_surface_m2,
                    aur.exceeds_max_requires_council,
                    aur.requires_street_width_min_m,
                    aur.requires_frontage_min_m,
                    aur.requires_frontage_max_m,
                    aur.min_surface_m2,
                    aur.special_condition,
                    aur.source_version_id
                FROM activity_use_rules aur
                JOIN source_versions sv ON sv.id = aur.source_version_id
                WHERE aur.activity_id = %s
                  AND sv.status IN ('active', 'ingested')
                ORDER BY
                    (sv.status = 'active') DESC,
                    COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
                    sv.id DESC,
                    aur.mixtura
                """,
                (activity_id,),
            )
            rows = await cur.fetchall()

        result: dict[int, dict[str, Any]] = {}
        for row in rows:
            mixtura = int(row[1])
            if mixtura in result:
                continue
            result[mixtura] = {
                "id": row[0],
                "raw_value": row[2],
                "status": row[3],
                "max_surface_m2": row[4],
                "exceeds_max_requires_council": bool(row[5]),
                "requires_street_width_min_m": row[6],
                "requires_frontage_min_m": row[7],
                "requires_frontage_max_m": row[8],
                "min_surface_m2": row[9],
                "special_condition": row[10],
                "source_version_id": row[11],
            }
        return result
