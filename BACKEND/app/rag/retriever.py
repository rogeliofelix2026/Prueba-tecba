"""Genera el embedding de la consulta y recupera evidencia documental."""

from app.core.config import settings
from app.integrations.ollama import OllamaClient
from app.repositories.rag import RagRepository


class RagRetriever:
    def __init__(self, ollama: OllamaClient) -> None:
        self.ollama = ollama
        self.repo = RagRepository()

    async def retrieve(
        self,
        question: str,
        embedding_model_id: int | None,
        activity_code: str | None = None,
    ) -> list[dict]:
        if embedding_model_id is None or not settings.rag_enabled:
            return []
        embedding = await self.ollama.embed(question)
        return await self.repo.search(
            embedding,
            question,
            embedding_model_id,
            settings.rag_top_k,
            activity_code=activity_code,
        )
