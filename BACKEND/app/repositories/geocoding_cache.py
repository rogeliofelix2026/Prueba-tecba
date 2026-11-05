"""Compatibilidad para el antiguo repositorio de caché; delega al contrato final."""

from typing import Any

from app.repositories.geocoding import GeocodingRepository


class GeocodingCacheRepository:
    """Adaptador fino para código legado que todavía importe este repositorio."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        self._repo = GeocodingRepository()

    async def get_valid(self, query_key: str) -> dict[str, Any] | None:
        return await self._repo.get(query_key)
