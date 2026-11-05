"""Busca los identificadores de modelos de IA activos registrados en la base de datos."""

from app.core.database import connection


class AIModelRepository:
    async def id_for(self, provider: str, model_name: str, model_type: str) -> int | None:
        async with connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                    SELECT id
                    FROM ai_models
                    WHERE provider = %s
                      AND model_name = %s
                      AND model_type = %s
                      AND is_active = TRUE
                    LIMIT 1
                    """,
                (provider, model_name, model_type),
            )
            row = await cur.fetchone()
            return row[0] if row else None
