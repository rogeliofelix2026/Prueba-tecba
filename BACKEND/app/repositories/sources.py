"""Metadatos de procedencia/versionado para auditar cada respuesta."""
from app.core.database import connection


class SourceRepository:
    async def get_versions(self, source_version_ids: set[int]) -> list[dict]:
        ids = sorted({int(value) for value in source_version_ids if value is not None})
        if not ids:
            return []
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT sv.id, s.code, s.name, s.publisher, sv.version_label,
                       sv.status, s.canonical_url, sv.checksum_sha256,
                       sv.published_at, sv.effective_from, sv.effective_to
                FROM public.source_versions sv
                JOIN public.sources s ON s.id = sv.source_id
                WHERE sv.id = ANY(%s)
                ORDER BY s.code, sv.id
                """,
                (ids,),
            )
            rows = await cur.fetchall()
        return [
            {
                "source_version_id": row[0],
                "code": row[1],
                "name": row[2],
                "publisher": row[3],
                "version": row[4],
                "status": row[5],
                "url": row[6],
                "checksum_sha256": row[7],
                "published_at": row[8].isoformat() if row[8] else None,
                "effective_from": row[9].isoformat() if row[9] else None,
                "effective_to": row[10].isoformat() if row[10] else None,
            }
            for row in rows
        ]
