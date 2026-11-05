"""
Adaptador asíncrono para los endpoints de USIG utilizados por geocodificación y territorio.

Gestiona HTTP, reintentos, límite de concurrencia y respuestas JSON/JSONP. `USIGClient`
se crea normalmente durante el lifespan de FastAPI y se libera con `close()`.
"""

import asyncio
import json
import logging
import random
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class USIGClientError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class USIGClient:
    """Adaptador asíncrono de USIG con pooling, límite de concurrencia y reintentos."""

    def __init__(
        self,
        rest_url: str,
        root_url: str,
        geocoder_url: str,
        timeout: float = 10.0,
        max_retries: int = 2,
        max_concurrency: int = 20,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.rest_url = rest_url.rstrip("/")
        self.root_url = root_url.rstrip("/")
        self.geocoder_url = geocoder_url.rstrip("/")
        self.max_retries = max(0, max_retries)
        self._created_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=3.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=30),
        )
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._timeout = httpx.Timeout(timeout, connect=3.0)

    async def close(self) -> None:
        if self._created_client:
            await self._client.aclose()

    @staticmethod
    def parse_response(text: str) -> Any:
        value = text.strip().rstrip(";")
        if value.startswith("(") and value.endswith(")"):
            value = value[1:-1].strip()
        jsonp_match = re.match(r"^[a-zA-Z0-9_$.]+\s*\((.*)\)$", value, re.DOTALL)
        if jsonp_match:
            value = jsonp_match.group(1).strip()
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise USIGClientError("USIG devolvió una respuesta que no es JSON válido.") from exc

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        async with self._semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await self._client.get(url, params=params, timeout=self._timeout)
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if "json" in content_type:
                        try:
                            return response.json()
                        except json.JSONDecodeError:
                            pass
                    return self.parse_response(response.text)
                except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                    retryable = (
                        isinstance(exc, httpx.RequestError)
                        or exc.response.status_code == 429
                        or exc.response.status_code >= 500
                    )
                    if attempt >= self.max_retries or not retryable:
                        status = (
                            exc.response.status_code
                            if isinstance(exc, httpx.HTTPStatusError)
                            else None
                        )
                        raise USIGClientError(
                            "No se pudo completar la petición a USIG.", status
                        ) from exc
                    delay = min(3.0, 0.35 * (2**attempt)) + random.uniform(0, 0.15)
                    logger.warning(
                        "Reintentando USIG en %.2fs (intento %d/%d)",
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)

        raise USIGClientError("No se pudo completar la petición a USIG.")

    async def normalize_and_geocode(self, street: str, height: int) -> dict[str, Any]:
        return await self._get(
            f"{self.rest_url}/normalizar_y_geocodificar_direcciones/",
            {"calle": street, "altura": height, "desambiguar": 1},
        )

    async def convert_gkba_to_lonlat(self, x: float, y: float) -> dict[str, Any]:
        return await self._get(
            f"{self.rest_url}/convertir_coordenadas/",
            {"x": x, "y": y, "output": "lonlat"},
        )

    async def useful_data(self, x: float, y: float) -> dict[str, Any]:
        return await self._get(f"{self.root_url}/datos_utiles", {"x": x, "y": y})

    async def adjacent_streets(self, street_code: int, height: int) -> dict[str, Any]:
        return await self._get(
            f"{self.rest_url}/obtener_calles_adyacentes/",
            {"cod_calle": street_code, "altura": height},
        )

    async def smp(self, street_code: int, height: int) -> Any:
        return await self._get(
            f"{self.geocoder_url}/smp",
            {"cod_calle": street_code, "altura": height},
        )

    async def reverse_geocoding(self, longitude: float, latitude: float) -> dict[str, Any]:
        return await self._get(
            f"{self.geocoder_url}/reversegeocoding",
            {"x": longitude, "y": latitude},
        )
