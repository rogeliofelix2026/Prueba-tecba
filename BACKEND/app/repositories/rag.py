"""Recuperación híbrida con pgvector + full-text según el schema final."""

from typing import Any

from pgvector import HalfVector as PgHalfVector

from app.core.config import settings
from app.core.database import connection


class RagRepository:
    async def search(
        self,
        query_embedding: list[float],
        query_text: str,
        embedding_model_id: int | None,
        top_k: int | None = None,
        activity_code: str | None = None,
    ) -> list[dict[str, Any]]:
        del activity_code  # El schema MVP no guarda metadata por chunk para filtrar por actividad.
        if embedding_model_id is None:
            return []

        top_k = top_k or settings.rag_top_k
        candidate_limit = max(top_k * settings.rag_candidate_multiplier, top_k)
        query_vector = PgHalfVector(query_embedding)

        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                WITH vector_candidates AS (
                    SELECT
                        dc.id,
                        1.0 - LEAST(dc.embedding <=> %s, 1.0) AS vector_score
                    FROM document_chunks dc
                    JOIN documents d ON d.id = dc.document_id
                    JOIN source_resources sr ON sr.id = d.source_resource_id
                    JOIN source_versions sv ON sv.id = sr.source_version_id
                    WHERE dc.embedding IS NOT NULL
                      AND dc.embedding_model_id = %s
                      AND sv.status IN ('active', 'ingested')
                    ORDER BY dc.embedding <=> %s
                    LIMIT %s
                ),
                lexical_candidates AS (
                    SELECT
                        dc.id,
                        ts_rank_cd(
                            to_tsvector('spanish', dc.content),
                            plainto_tsquery('spanish', %s)
                        ) AS lexical_rank
                    FROM document_chunks dc
                    JOIN documents d ON d.id = dc.document_id
                    JOIN source_resources sr ON sr.id = d.source_resource_id
                    JOIN source_versions sv ON sv.id = sr.source_version_id
                    WHERE to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', %s)
                      AND sv.status IN ('active', 'ingested')
                    ORDER BY lexical_rank DESC
                    LIMIT %s
                ),
                candidate_ids AS (
                    SELECT id FROM vector_candidates
                    UNION
                    SELECT id FROM lexical_candidates
                )
                SELECT
                    dc.id,
                    dc.chunk_index,
                    d.document_key,
                    d.title,
                    sv.id AS source_version_id,
                    dc.content,
                    dc.heading_path,
                    dc.page_from,
                    dc.page_to,
                    COALESCE(vc.vector_score, 0.0) AS vector_score,
                    COALESCE(
                        lc.lexical_rank / (1.0 + lc.lexical_rank),
                        0.0
                    ) AS lexical_score,
                    (
                        %s * COALESCE(vc.vector_score, 0.0)
                        +
                        %s * COALESCE(
                            lc.lexical_rank / (1.0 + lc.lexical_rank),
                            0.0
                        )
                    ) AS score
                FROM candidate_ids ids
                JOIN document_chunks dc ON dc.id = ids.id
                JOIN documents d ON d.id = dc.document_id
                JOIN source_resources sr ON sr.id = d.source_resource_id
                JOIN source_versions sv ON sv.id = sr.source_version_id
                LEFT JOIN vector_candidates vc ON vc.id = dc.id
                LEFT JOIN lexical_candidates lc ON lc.id = dc.id
                ORDER BY score DESC, dc.id
                LIMIT %s
                """,
                (
                    query_vector,
                    embedding_model_id,
                    query_vector,
                    candidate_limit,
                    query_text,
                    query_text,
                    candidate_limit,
                    settings.rag_vector_weight,
                    settings.rag_lexical_weight,
                    top_k,
                ),
            )
            rows = await cur.fetchall()

        return [
            {
                "document_chunk_id": row[0],
                "reference_key": f"{row[2]}#chunk-{row[1]}",
                "chunk_index": row[1],
                "document_key": row[2],
                "title": row[3],
                "source_version_id": row[4],
                "content": row[5],
                "heading_path": row[6],
                "page_from": row[7],
                "page_to": row[8],
                "vector_score": float(row[9]),
                "lexical_score": float(row[10]),
                "score": float(row[11]),
            }
            for row in rows
        ]
