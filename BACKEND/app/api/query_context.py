"""Contratos internos/externos del resultado de una consulta."""

from dataclasses import asdict, dataclass, field
from typing import Any

from pydantic import BaseModel, Field


def omit_empty_values(value: Any) -> Any:
    """Quita nulls y cadenas vacías de payloads externos sin descartar 0/False."""
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if item is None or (isinstance(item, str) and not item.strip()):
                continue
            nested = omit_empty_values(item)
            if nested is None or (isinstance(nested, str) and not nested.strip()):
                continue
            cleaned[key] = nested
        return cleaned
    if isinstance(value, list):
        return [
            nested for item in value
            if item is not None and not (isinstance(item, str) and not item.strip())
            for nested in [omit_empty_values(item)]
            if nested is not None and not (isinstance(nested, str) and not nested.strip())
        ]
    return value


@dataclass(slots=True)
class GeocodingResult:
    input_address: str
    normalized_address: str | None
    street_code: int | None
    height: int | None
    gkba_x: float | None
    gkba_y: float | None
    latitude: float | None
    longitude: float | None
    smp: str | None
    source_version_id: int | None = None
    useful_data: dict[str, Any] = field(default_factory=dict)
    adjacent_streets: list[dict[str, Any]] = field(default_factory=list)
    reverse_geocoding: dict[str, Any] = field(default_factory=dict)
    parcel_geometry_geojson: dict[str, Any] | None = None
    usig_raw: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    from_cache: bool = False

    @classmethod
    def from_cached(cls, cached: dict[str, Any]) -> "GeocodingResult":
        normalized = None
        if cached.get("normalized_street") and cached.get("height") is not None:
            normalized = f"{cached['normalized_street']} {cached['height']}"

        response = cached.get("response_json") or {}
        gkba = response.get("gkba") if isinstance(response, dict) else {}
        useful_data = response.get("useful_data", {}) if isinstance(response, dict) else {}
        useful_data = omit_empty_values(useful_data)
        adjacent = response.get("adjacent_streets", []) if isinstance(response, dict) else []
        reverse = response.get("reverse_geocoding", {}) if isinstance(response, dict) else {}
        warnings = response.get("warnings", []) if isinstance(response, dict) else []

        return cls(
            input_address=cached["input_address"],
            normalized_address=normalized,
            street_code=cached.get("street_code"),
            height=cached.get("height"),
            gkba_x=gkba.get("x") if isinstance(gkba, dict) else None,
            gkba_y=gkba.get("y") if isinstance(gkba, dict) else None,
            latitude=cached.get("latitude"),
            longitude=cached.get("longitude"),
            smp=cached.get("smp"),
            source_version_id=cached.get("source_version_id"),
            useful_data=useful_data if isinstance(useful_data, dict) else {},
            adjacent_streets=adjacent if isinstance(adjacent, list) else [],
            reverse_geocoding=reverse if isinstance(reverse, dict) else {},
            parcel_geometry_geojson=response.get("parcel_geometry_geojson") if isinstance(response, dict) and isinstance(response.get("parcel_geometry_geojson"), dict) else None,
            usig_raw=response,
            warnings=warnings if isinstance(warnings, list) else [],
            from_cache=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Consulta(BaseModel):
    texto_original: str
    actividad_original: str
    direccion_original: str | None = None


class Actividad(BaseModel):
    id: int | None = None
    codigo: str | None = None
    nombre: str
    categoria: str | None = None
    estado_mapeo: str | None = None
    source_version_id: int | None = None
    alias_source_version_id: int | None = None


class Ubicacion(BaseModel):
    direccion_original: str | None = None
    direccion_normalizada: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    smp: str | None = None
    codigo_calle: int | None = None
    altura: int | None = None
    advertencias: list[str] = Field(default_factory=list)
    desde_cache: bool = False
    source_version_id: int | None = None


class Territorio(BaseModel):
    parcela: dict[str, Any] | None = None
    reglas_urbanisticas: list[dict[str, Any]] = Field(default_factory=list)
    usos_suelo: list[dict[str, Any]] = Field(default_factory=list)
    compatibilidad_urbanistica: dict[str, Any] | None = None


class Procedimiento(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    prioridad: int = 100
    notas: str | None = None
    requisitos: list[dict[str, Any]] = Field(default_factory=list)
    documentos: list[dict[str, Any]] = Field(default_factory=list)
    pasos: list[dict[str, Any]] = Field(default_factory=list)
    reglas: list[dict[str, Any]] = Field(default_factory=list)
    source_version_id: int | None = None


class Fuente(BaseModel):
    source_version_id: int
    codigo: str
    nombre: str
    publisher: str | None = None
    version: str
    estado: str
    url: str | None = None


class QueryContext(BaseModel):
    consulta: Consulta
    actividad: Actividad
    ubicacion: Ubicacion | None = None
    territorio: Territorio = Field(default_factory=Territorio)
    procedimientos: list[Procedimiento] = Field(default_factory=list)
    clasificacion_tramite: dict[str, Any] | None = None
    fuentes: list[Fuente] = Field(default_factory=list)


class QueryResponse(BaseModel):
    query_id: str
    status: str
    answer: str | None = None
    context: QueryContext
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    links: dict[str, str | None] = Field(default_factory=dict)
