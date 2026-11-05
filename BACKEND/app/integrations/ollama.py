"""
Adaptador asíncrono para Ollama encargado de chat y generación de embeddings.

Reutiliza un cliente HTTP, limita la concurrencia por tipo de operación y reintenta errores
transitorios. `OllamaClient` debe cerrarse al finalizar su ciclo de vida mediante `close()`.
"""

import asyncio
import logging
import random
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaClientError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OllamaClient:
    """Adaptador asíncrono y reutilizable para Ollama."""

    def __init__(
        self,
        base_url: str,
        chat_model: str,
        embedding_model: str,
        chat_timeout: float = 120.0,
        embed_timeout: float = 120.0,
        max_retries: int = 2,
        chat_max_concurrency: int = 2,
        embed_max_concurrency: int = 2,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.max_retries = max(0, max_retries)
        self._created_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(chat_timeout, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=20),
        )
        self._chat_timeout = httpx.Timeout(chat_timeout, connect=5.0)
        self._embed_timeout = httpx.Timeout(embed_timeout, connect=5.0)
        self._chat_semaphore = asyncio.Semaphore(max(1, chat_max_concurrency))
        self._embed_semaphore = asyncio.Semaphore(max(1, embed_max_concurrency))

    async def close(self) -> None:
        if self._created_client:
            await self._client.aclose()

    @staticmethod
    def _retryable(exc: BaseException) -> bool:
        if isinstance(exc, httpx.RequestError):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code == 429 or exc.response.status_code >= 500
        return False

    async def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        timeout: httpx.Timeout,
    ) -> dict[str, Any]:
        last_error: BaseException | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise OllamaClientError("Ollama devolvió una respuesta con formato inválido.")
                return data
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= self.max_retries or not self._retryable(exc):
                    status = (
                        exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                    )
                    raise OllamaClientError(
                        "No se pudo completar la petición a Ollama.", status
                    ) from exc
                delay = min(4.0, 0.5 * (2**attempt)) + random.uniform(0, 0.2)
                logger.warning(
                    "Reintentando Ollama en %.2fs (intento %d/%d)",
                    delay,
                    attempt + 1,
                    self.max_retries,
                )
                await asyncio.sleep(delay)
            except ValueError as exc:
                raise OllamaClientError("Ollama devolvió JSON inválido.") from exc

        raise OllamaClientError("No se pudo completar la petición a Ollama.") from last_error

    async def embed(self, text: str) -> list[float]:
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with self._embed_semaphore:
            data = await self._post(
                "/api/embed",
                {"model": self.embedding_model, "input": texts},
                self._embed_timeout,
            )
        embeddings = data.get("embeddings") or []
        if len(embeddings) != len(texts):
            raise OllamaClientError(
                f"Ollama devolvió {len(embeddings)} embeddings para {len(texts)} textos."
            )
        return embeddings

    async def chat(self, system: str, user: str) -> str:
        return await self._chat_with_format(system, user, json_mode=False)

    async def chat_json(self, system: str, user: str) -> str:
        """Solicita salida JSON al modelo; el consumidor igual debe validarla."""
        return await self._chat_with_format(system, user, json_mode=True)

    async def _chat_with_format(self, system: str, user: str, *, json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0.0 if json_mode else 0.2, "num_predict": 700 if json_mode else 900},
        }
        if json_mode:
            # Ollama's JSON mode constrains the output format, not its truth.
            # Parsing, evidence checks and catalog validation remain mandatory.
            payload["format"] = "json"
        async with self._chat_semaphore:
            data = await self._post("/api/chat", payload, self._chat_timeout)
        text = str(data.get("message", {}).get("content", "")).strip()
        if not text:
            raise OllamaClientError("Ollama no devolvió respuesta de texto.")
        return text
