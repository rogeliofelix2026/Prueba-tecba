"""Orquesta USIG, caché y enriquecimiento de una dirección."""

import asyncio
import logging
import re
import unicodedata
from typing import Any

from app.api.query_context import GeocodingResult, omit_empty_values
from app.core.config import settings
from app.core.smp import normalize_smp
from app.integrations.usig import USIGClient, USIGClientError

logger = logging.getLogger(__name__)

ADDRESS_RE = re.compile(r"^(.*?)\s+(\d+)\s*$")


class AddressNotFoundError(ValueError):
    """USIG respondió correctamente, pero no encontró una dirección candidata."""

def normalize_cache_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def extract_smp(value: Any) -> str | None:
    """Extrae un SMP de las variantes habituales de respuesta de USIG."""
    if isinstance(value, str):
        return normalize_smp(value)

    if isinstance(value, dict):
        # Caso directo: {"smp": "003-035-019"} o cualquier capitalización.
        for key, item in value.items():
            if str(key).casefold() == "smp":
                if isinstance(item, str):
                    found = normalize_smp(item)
                    if found:
                        return found
                found = extract_smp(item)
                if found:
                    return found

        # Algunas respuestas pueden separar la clave catastral en componentes.
        normalized_keys = {str(key).casefold(): item for key, item in value.items()}
        section = normalized_keys.get("seccion", normalized_keys.get("sección"))
        block = normalized_keys.get("manzana")
        parcel = normalized_keys.get("parcela")
        if all(item is not None for item in (section, block, parcel)):
            composed = f"{section}-{block}-{parcel}"
            found = normalize_smp(composed)
            if found:
                return found

        # Recorrer payloads anidados (resultado, parcela, data, etc.).
        for item in value.values():
            found = extract_smp(item)
            if found:
                return found

    elif isinstance(value, list):
        for item in value:
            found = extract_smp(item)
            if found:
                return found

    return None


def extract_parcel_geometry(value: Any) -> dict[str, Any] | None:
    """Extrae un polígono solo desde un contenedor identificado como parcela.

    Evita cachear por error geometrías de escuelas, hospitales, radios u otros
    objetos que puedan aparecer en `datos útiles`. Una coordenada Point nunca se
    convierte en polígono.
    """
    geometry_keys = {"geometry", "geom", "polygon", "poligono", "geojson", "feature"}
    parcel_keys = {
        "parcel", "parcela", "parcelgeometry", "geometryparcel", "geometriaparcel",
        "parcelageometria", "poligonoparcela", "poligonocatastral", "catastralparcel",
        "smp", "nomenclaturacatastral",
    }
    neutral_containers = {"usefuldata", "reversegeocoding", "data", "resultado", "result", "response"}

    def visit(node: Any, parcel_context: bool = False) -> dict[str, Any] | None:
        if isinstance(node, dict):
            geometry_type = node.get("type")
            if geometry_type in {"Polygon", "MultiPolygon"} and isinstance(node.get("coordinates"), list):
                return {"type": geometry_type, "coordinates": node["coordinates"]} if parcel_context else None

            if geometry_type == "Feature" and isinstance(node.get("geometry"), dict):
                properties = node.get("properties") or {}
                property_keys = {str(key).casefold().replace("_", "") for key in properties} if isinstance(properties, dict) else set()
                feature_is_parcel = parcel_context or bool(property_keys & {
                    "smp", "nomenclaturacatastral", "idparcela", "parcelid", "parcela_id"
                })
                found = visit(node["geometry"], feature_is_parcel)
                if found:
                    return found

            # Solo traversar campos que declaren explícitamente parcela/SMP o un
            # campo geométrico dentro de un contexto ya identificado como parcela.
            for key, child in node.items():
                normalized_key = "".join(ch for ch in str(key).casefold() if ch.isalnum())
                child_is_parcel = parcel_context or normalized_key in parcel_keys
                if child_is_parcel or normalized_key in neutral_containers or (parcel_context and normalized_key in geometry_keys):
                    found = visit(child, child_is_parcel)
                    if found:
                        return found
        elif isinstance(node, list):
            if parcel_context:
                for child in node:
                    found = visit(child, True)
                    if found:
                        return found
        return None

    return visit(value)


def _number(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"USIG no devolvió una coordenada válida para '{name}'.") from exc


class GeocodingService:
    def __init__(self, usig: USIGClient, repo=None) -> None:
        self.usig = usig
        if repo is None:
            from app.repositories.geocoding import GeocodingRepository

            repo = GeocodingRepository()
        self.repo = repo
        self._inflight: dict[str, asyncio.Task[GeocodingResult]] = {}

    async def geocode(self, address: str) -> GeocodingResult:
        street, height = self._parse_address(address)
        cache_key = self._normalize_query_key(street, height)

        cached = await self.repo.get(cache_key, "USIG")
        cached_smp = extract_smp(cached.get("smp")) if cached else None
        if cached and cached_smp:
            cached["smp"] = cached_smp
            return GeocodingResult.from_cached(cached)
        if cached:
            refreshed = await self._refresh_cached_smp(cached)
            if refreshed is not None:
                return refreshed

        task = self._inflight.get(cache_key)
        if task is None:
            task = asyncio.create_task(self._geocode_uncached(address, street, height, cache_key))
            self._inflight[cache_key] = task
            task.add_done_callback(lambda done: self._discard_inflight(cache_key, done))

        return await asyncio.shield(task)

    def _discard_inflight(self, cache_key: str, task: asyncio.Task[GeocodingResult]) -> None:
        if self._inflight.get(cache_key) is task:
            self._inflight.pop(cache_key, None)

    async def _geocode_uncached(
        self, address: str, street: str, height: int, cache_key: str
    ) -> GeocodingResult:
        normalized = await self.usig.normalize_and_geocode(street, height)
        item = self._extract_first_direction(normalized, address)
        try:
            street_code = int(item["CodigoCalle"])
            normalized_street = str(item["Calle"])
            normalized_height = int(item["Altura"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("USIG devolvió una dirección normalizada incompleta.") from exc

        geo = normalized.get("GeoCodificacion") or {}
        gkba_x = _number(geo.get("x"), "gkba_x")
        gkba_y = _number(geo.get("y"), "gkba_y")

        converted = await self.usig.convert_gkba_to_lonlat(gkba_x, gkba_y)
        result = converted.get("resultado") if isinstance(converted, dict) else None
        coords = result if isinstance(result, dict) else converted
        longitude = self._read_coordinate(coords, ("x", "lon", "lng"), "longitude")
        latitude = self._read_coordinate(coords, ("y", "lat"), "latitude")

        useful, adjacent, smp_raw, reverse = await asyncio.gather(
            self._fetch_useful_data(gkba_x, gkba_y),
            self._fetch_adjacent_streets(street_code, normalized_height),
            self._fetch_smp(street_code, normalized_height),
            self._fetch_reverse_geocoding(longitude, latitude),
        )

        warning_codes: list[str] = []
        for value in (useful, adjacent, smp_raw, reverse):
            if isinstance(value, _SupplementaryFailure):
                warning_codes.append(value.code)

        useful_data = {} if isinstance(useful, _SupplementaryFailure) else omit_empty_values(useful)
        adjacent_data = [] if isinstance(adjacent, _SupplementaryFailure) else adjacent
        raw_smp = None if isinstance(smp_raw, _SupplementaryFailure) else smp_raw
        reverse_data = {} if isinstance(reverse, _SupplementaryFailure) else reverse

        # Resolver SMP determinísticamente: respuesta directa -> puerta oficial de
        # reverse geocoding -> parcela del reverse geocoding. Se conserva siempre
        # el payload bruto del primer endpoint en `usig_raw.smp`.
        smp_value = extract_smp(raw_smp) if raw_smp is not None else None
        smp_resolution: dict[str, Any] = {
            "status": "unresolved",
            "source": None,
            "requested_height": normalized_height,
        }
        if smp_value:
            smp_resolution.update({"status": "resolved", "source": "usig_smp"})
        else:
            official_door = reverse_data.get("puerta") if isinstance(reverse_data, dict) else None
            official_door_height = None
            if isinstance(official_door, str) and official_door.strip():
                try:
                    _, official_door_height = self._parse_address(official_door)
                except ValueError:
                    official_door_height = None

            if official_door_height is not None:
                smp_official_door_raw = await self._fetch_smp(street_code, official_door_height)
                if not isinstance(smp_official_door_raw, _SupplementaryFailure):
                    smp_value = extract_smp(smp_official_door_raw)
                if smp_value:
                    smp_resolution.update({
                        "status": "resolved",
                        "source": "usig_smp_official_door",
                        "official_door_height": official_door_height,
                    })

            if not smp_value and isinstance(reverse_data, dict):
                smp_value = extract_smp(reverse_data.get("parcela"))
                if smp_value:
                    smp_resolution.update({
                        "status": "resolved",
                        "source": "reverse_geocoding_parcela",
                    })

            if not smp_value and official_door_height is not None:
                smp_resolution["official_door_height"] = official_door_height

        raw_response = {
            "normalization_geocoding": normalized,
            "wgs84": converted,
            "smp": raw_smp,
            "smp_resolution": smp_resolution,
            "gkba": {"x": gkba_x, "y": gkba_y},
            "useful_data": useful_data,
            "adjacent_streets": adjacent_data,
            "reverse_geocoding": reverse_data,
            "warnings": warning_codes,
            "provider_version": "rest+geocoder2.2",
        }
        parcel_geometry = extract_parcel_geometry({"useful_data": useful_data, "reverse_geocoding": reverse_data, "smp": raw_smp})
        if parcel_geometry:
            raw_response["parcel_geometry_geojson"] = parcel_geometry
        payload = {
            "query_key": cache_key,
            "input_address": address,
            "normalized_street": normalized_street,
            "street_code": street_code,
            "height": normalized_height,
            "latitude": latitude,
            "longitude": longitude,
            "smp": smp_value,
            "response_json": raw_response,
        }
        ttl = (
            settings.usig_partial_cache_ttl_hours
            if warning_codes
            else settings.usig_cache_ttl_hours
        )
        source_version_id = await self.repo.upsert(payload, ttl)

        return GeocodingResult(
            input_address=address,
            normalized_address=f"{normalized_street} {normalized_height}",
            street_code=street_code,
            height=normalized_height,
            gkba_x=gkba_x,
            gkba_y=gkba_y,
            latitude=latitude,
            longitude=longitude,
            smp=smp_value,
            source_version_id=source_version_id,
            useful_data=useful_data,
            adjacent_streets=adjacent_data,
            reverse_geocoding=reverse_data,
            parcel_geometry_geojson=parcel_geometry,
            usig_raw=raw_response,
            warnings=warning_codes,
        )


    async def _refresh_cached_smp(self, cached: dict[str, Any]) -> GeocodingResult | None:
        """Completa una entrada de caché parcial sin repetir toda la geocodificación."""
        street_code = cached.get("street_code")
        height = cached.get("height")
        if street_code is None or height is None:
            return None

        smp_raw = await self._fetch_smp(int(street_code), int(height))
        if isinstance(smp_raw, _SupplementaryFailure):
            return None

        smp_value = extract_smp(smp_raw)
        if not smp_value:
            logger.warning(
                "USIG respondió al endpoint SMP pero no se pudo extraer un SMP: %r",
                smp_raw,
            )
            return None

        await self.repo.update_smp(cached["query_key"], "USIG", smp_value)
        cached["smp"] = smp_value
        return GeocodingResult.from_cached(cached)

    async def _fetch_useful_data(self, x: float, y: float):
        try:
            return await self.usig.useful_data(x, y)
        except USIGClientError as exc:
            logger.warning("USIG useful_data falló: %s", exc)
            return _SupplementaryFailure("usig_useful_data_unavailable")

    async def _fetch_adjacent_streets(self, street_code: int, height: int):
        try:
            result = await self.usig.adjacent_streets(street_code, height)
            return result.get("calles", []) if isinstance(result, dict) else []
        except USIGClientError as exc:
            logger.warning("USIG adjacent_streets falló: %s", exc)
            return _SupplementaryFailure("usig_adjacent_streets_unavailable")

    async def _fetch_smp(self, street_code: int, height: int):
        try:
            return await self.usig.smp(street_code, height)
        except USIGClientError as exc:
            logger.warning("USIG SMP falló: %s", exc)
            return _SupplementaryFailure("usig_smp_unavailable")

    async def _fetch_reverse_geocoding(self, longitude: float, latitude: float):
        try:
            return await self.usig.reverse_geocoding(longitude, latitude)
        except USIGClientError as exc:
            logger.warning("USIG reverse_geocoding falló: %s", exc)
            return _SupplementaryFailure("usig_reverse_geocoding_unavailable")

    @staticmethod
    def _read_coordinate(data: dict[str, Any], keys: tuple[str, ...], name: str) -> float:
        for key in keys:
            if key in data and data[key] not in (None, ""):
                return _number(data[key], name)
        raise ValueError(f"USIG no devolvió '{name}'.")

    @staticmethod
    def _parse_address(address: str) -> tuple[str, int]:
        match = ADDRESS_RE.fullmatch(address.strip())
        if not match:
            raise ValueError(
                "La dirección debe contener calle y altura, por ejemplo: Corrientes 2500"
            )
        street, height_text = match.groups()
        return street.strip(), int(height_text)

    @staticmethod
    def _normalize_query_key(street: str, height: int) -> str:
        return f"{normalize_cache_text(street)}|{height}"

    @staticmethod
    def _extract_first_direction(
        normalized: dict[str, Any], original_address: str
    ) -> dict[str, Any]:
        items = (
            normalized.get("Normalizacion", {})
            .get("DireccionesCalleAltura", {})
            .get("direcciones", [])
        )
        if not items:
            raise AddressNotFoundError(f"USIG no encontró la dirección: {original_address}")
        return items[0]

    @staticmethod
    def map_url(result: GeocodingResult) -> str | None:
        if result.latitude is None or result.longitude is None:
            return None
        return (
            "https://mapa.usig.buenosaires.gob.ar/"
            f"?lat={result.latitude:.7f}&lng={result.longitude:.7f}"
        )


class _SupplementaryFailure:
    __slots__ = ("code",)

    def __init__(self, code: str) -> None:
        self.code = code
