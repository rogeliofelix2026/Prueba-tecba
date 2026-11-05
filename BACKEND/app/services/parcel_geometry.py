"""Proveedor de polígonos catastrales desde una fuente oficial local/montada.

USIG da la posición y el SMP, pero su API pública de geocodificación no expone un
endpoint documentado para descargar el polígono de la parcela. Este adaptador busca
por SMP en el recurso oficial Parcelas, una sola geometría por llamada. En producción
se recomienda un GeoPackage con índice de atributo sobre SMP para no escanear un
GeoJSON completo en cada caché-miss.
"""
from __future__ import annotations

import asyncio
import hashlib
import itertools
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ParcelGeometrySourceError(RuntimeError):
    """La fuente geométrica está configurada pero no se puede consultar con seguridad."""


@dataclass(frozen=True, slots=True)
class ParcelGeometryFeature:
    smp: str
    geometry: dict[str, Any]
    checksum_sha256: str
    source_path: str
    source_crs: str


def canonical_smp(value: str) -> str:
    text = re.sub(r"\s*[-–—]\s*", "-", value.strip()).upper()
    text = re.sub(r"\s+", "", text)
    if not re.fullmatch(r"\d{1,3}-[A-Z0-9]+-[A-Z0-9]+", text):
        raise ValueError(f"SMP inválido: {value!r}")
    section, block, parcel = text.split("-")
    return f"{section.zfill(3)}-{block}-{parcel}"


def _norm_col(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(char for char in value if not unicodedata.combining(char)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


class ParcelGeometryProvider:
    def __init__(self, source_path: str | Path | None, layer: str | None = None) -> None:
        self.source_path = Path(source_path).expanduser() if source_path else None
        self.layer = layer or None

    @property
    def configured(self) -> bool:
        return self.source_path is not None

    async def fetch(self, smp: str) -> ParcelGeometryFeature:
        if self.source_path is None:
            raise ParcelGeometrySourceError("PARCEL_GEOMETRY_SOURCE_NOT_CONFIGURED")
        return await asyncio.to_thread(self._fetch_sync, smp)

    def _fetch_sync(self, smp: str) -> ParcelGeometryFeature:
        path = self.source_path
        assert path is not None
        if not path.is_file():
            raise ParcelGeometrySourceError(f"No existe la fuente geométrica configurada: {path}")
        try:
            import geopandas as gpd
            import pyogrio
            from shapely.geometry import mapping
            from shapely.validation import make_valid
        except ImportError as exc:
            raise ParcelGeometrySourceError(
                "Faltan dependencias geoespaciales. Instalar requirements.txt (incluye geopandas y pyogrio)."
            ) from exc

        requested = canonical_smp(smp)
        try:
            info = pyogrio.read_info(path, layer=self.layer)
            fields = [str(field) for field in (info.get("fields") or [])]
            normalized = {_norm_col(field): field for field in fields}
            smp_field = next(
                (normalized[key] for key in ("smp", "smp_completa", "nomenclatura_catastral", "nomenclatura", "parcela_smp") if key in normalized),
                None,
            )
            if not smp_field:
                raise ParcelGeometrySourceError(
                    f"La fuente {path.name} no tiene una columna SMP reconocible. Campos: {fields}"
                )

            section, block, parcel = requested.split("-")
            section_variants = list(dict.fromkeys((section, section.zfill(2), str(int(section)))))
            # SMP sources sometimes use upper case in manzana and lower case in parcela
            # (for example 054-043B-001a). Generate exact spellings and query by equality
            # so a GeoPackage attribute index on `smp` can be used. Avoid UPPER(smp),
            # which prevents an ordinary index from accelerating the lookup.
            block_variants = list(dict.fromkeys((block, block.upper(), block.lower())))
            parcel_variants = list(dict.fromkeys((parcel, parcel.upper(), parcel.lower())))
            candidates = []
            for sec, blk, par in itertools.product(section_variants, block_variants, parcel_variants):
                candidates.append(f"{sec}-{blk}-{par}")
            candidates = list(dict.fromkeys(candidates))
            field_sql = '"' + smp_field.replace('"', '""') + '"'
            candidate_sql = ", ".join("'" + candidate.replace("'", "''") + "'" for candidate in candidates)
            # Single pass against flat GeoJSON and an index-assisted IN search for GPKG.
            where = f"{field_sql} IN ({candidate_sql})"
            frame = pyogrio.read_dataframe(
                path, layer=self.layer, where=where, columns=[smp_field], read_geometry=True,
            )
            if frame is None or len(frame) == 0:
                raise ParcelGeometrySourceError(f"La fuente oficial de parcelas no contiene el SMP {requested}.")
            if len(frame) != 1:
                raise ParcelGeometrySourceError(
                    f"La fuente devuelve {len(frame)} geometrías para {requested}; se rechaza elegir una arbitrariamente."
                )

            source_crs = str(frame.crs or info.get("crs") or "")
            if not source_crs:
                # El recurso oficial está publicado como application/geo+json; RFC 7946 usa WGS84.
                if path.suffix.casefold() in {".geojson", ".json"}:
                    frame = frame.set_crs("EPSG:4326", allow_override=True)
                    source_crs = "EPSG:4326 (GeoJSON RFC 7946)"
                else:
                    raise ParcelGeometrySourceError(
                        "La fuente no declara CRS. No se inferirá el CRS para SHP/GPKG."
                    )
            if frame.crs and str(frame.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
                frame = frame.to_crs("EPSG:4326")

            geometry = frame.geometry.iloc[0]
            if geometry is None or geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                raise ParcelGeometrySourceError("La fuente no devolvió un Polygon/MultiPolygon no vacío.")
            if not geometry.is_valid:
                geometry = make_valid(geometry)
                if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                    raise ParcelGeometrySourceError("La geometría inválida no pudo repararse como polígono.")
            geometry_json = mapping(geometry)
            canonical_json = json.dumps(geometry_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
            return ParcelGeometryFeature(
                smp=requested,
                geometry=geometry_json,
                checksum_sha256=digest,
                source_path=str(path.resolve()),
                source_crs=source_crs,
            )
        except ParcelGeometrySourceError:
            raise
        except Exception as exc:
            raise ParcelGeometrySourceError(
                f"No se pudo leer una geometría para {requested} desde {path.name}: {type(exc).__name__}: {exc}"
            ) from exc
