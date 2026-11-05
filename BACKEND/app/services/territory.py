"""Caso de uso territorial con caché de geometría parcelaria bajo demanda."""

from __future__ import annotations

import logging
from typing import Any

from app.api.query_context import GeocodingResult
from app.repositories.territory import TerritoryRepository
from app.services.parcel_geometry import ParcelGeometryProvider, ParcelGeometrySourceError

logger = logging.getLogger(__name__)


class TerritoryService:
    """Resuelve atributos territoriales y cachea solo los polígonos consultados."""

    def __init__(
        self, repo: TerritoryRepository, *, geometry_source_path: str | None = None,
        geometry_source_layer: str | None = None, geometry_source_version_id: int | None = None,
        cache_geometry_on_resolve: bool = False,
        geometry_provider: ParcelGeometryProvider | None = None,
    ) -> None:
        self.repo = repo
        self.geometry_provider = geometry_provider or ParcelGeometryProvider(geometry_source_path, geometry_source_layer)
        self.cache_geometry_on_resolve = cache_geometry_on_resolve
        self.geometry_source_version_id = geometry_source_version_id

    async def cache_geometry(self, parcel_id: int, geojson: dict[str, Any], source_version_id: int | None = None) -> bool:
        return await self.repo.cache_geometry(parcel_id, geojson, source_version_id)

    async def resolve(
        self, location: GeocodingResult | dict[str, Any] | None, include_geometry: bool = False,
    ) -> dict[str, Any]:
        if not location:
            return {
                "parcel": None, "smp": None, "urban_rules": [], "land_use": [],
                "resolution_status": "not_resolved", "candidate_parcels": [],
                "warnings": ["LOCATION_NOT_PROVIDED"],
            }

        if isinstance(location, GeocodingResult):
            smp, latitude, longitude = location.smp, location.latitude, location.longitude
        else:
            smp, latitude, longitude = location.get("smp"), location.get("latitude"), location.get("longitude")

        result = await self.repo.resolve(smp, latitude, longitude, include_geometry)
        parcel = result.get("parcel") or {}
        if not parcel or result.get("resolution_status") != "resolved":
            return result

        # geometry_source_version_id identifica una geometría guardada en parcel_geometries.
        # Cuando include_geometry=false el polígono no se serializa, pero la versión de caché
        # sigue permitiendo saber si ya existe.
        already_cached = parcel.get("geometry_source_version_id") is not None
        if not already_cached and self.cache_geometry_on_resolve:
            if not self.geometry_provider.configured:
                result.setdefault("warnings", []).append("PARCEL_GEOMETRY_SOURCE_NOT_CONFIGURED")
                parcel["geometry_status"] = "source_not_configured"
            elif self.geometry_source_version_id is None:
                # No adivinar la versión de un archivo externo a partir de la última
                # versión activa: podría etiquetar geometría vieja con metadatos nuevos.
                result.setdefault("warnings", []).append("PARCEL_GEOMETRY_SOURCE_VERSION_NOT_CONFIGURED")
                parcel["geometry_status"] = "source_version_not_configured"
            else:
                try:
                    feature = await self.geometry_provider.fetch(str(parcel.get("smp") or smp or ""))
                    stored = await self.repo.cache_geometry(
                        int(parcel["id"]), feature.geometry, self.geometry_source_version_id
                    )
                    if stored:
                        # Releer el resultado para que la versión de fuente y, si se pidió,
                        # el polígono provengan de PostGIS y no de la respuesta del proveedor.
                        result = await self.repo.resolve(smp, latitude, longitude, include_geometry)
                        parcel = result.get("parcel") or parcel
                        parcel["geometry_status"] = "cached" if parcel.get("geometry_source_version_id") else "cache_write_not_confirmed"
                    else:
                        parcel["geometry_status"] = "cache_write_failed"
                        result.setdefault("warnings", []).append("PARCEL_GEOMETRY_CACHE_WRITE_FAILED")
                except ParcelGeometrySourceError as exc:
                    logger.warning("No se pudo obtener geometría para smp=%s: %s", parcel.get("smp"), exc)
                    parcel["geometry_status"] = "source_not_found_or_invalid"
                    result.setdefault("warnings", []).append("PARCEL_GEOMETRY_SOURCE_FAILED")
                except Exception:
                    logger.exception("Fallo no fatal al obtener/cachear geometría smp=%s", parcel.get("smp"))
                    parcel["geometry_status"] = "cache_failed"
                    result.setdefault("warnings", []).append("PARCEL_GEOMETRY_CACHE_WRITE_FAILED")
        elif already_cached:
            parcel["geometry_status"] = "cached"
        else:
            parcel["geometry_status"] = "not_requested"

        if include_geometry and not (parcel or {}).get("geometry"):
            result.setdefault("warnings", []).append("PARCEL_GEOMETRY_NOT_INCLUDED")
        return result
