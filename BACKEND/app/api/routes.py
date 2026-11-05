"""Rutas HTTP v1: validación de entrada y traducción de errores a HTTP."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from app.api.query_context import QueryResponse
from app.core.config import settings
from app.integrations.ollama import OllamaClientError
from app.integrations.usig import USIGClientError
from app.services.geocoding import AddressNotFoundError



class ApiErrorDetails(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: Any | None = None


class ApiErrorResponse(BaseModel):
    """Formato estable utilizado por los handlers globales de main.py."""
    error: ApiErrorDetails


router = APIRouter(prefix="/api/v1")


class RequestModel(BaseModel):
    """Contrato HTTP tolerante con entradas del frontend y números finitos.

    Los campos desconocidos (p. ej. estado visual del formulario) no deben
    romper el flujo. La respuesta funcional indicará qué dato falta cuando no
    se pueda iniciar una resolución.
    """

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)


class GeocodingRequest(RequestModel):
    address: str = Field(
        min_length=3,
        max_length=250,
    )

    @field_validator("address")
    @classmethod
    def clean_address(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("La dirección debe tener al menos 3 caracteres después de normalizar espacios.")
        return cleaned


class TerritoryResolutionRequest(RequestModel):
    """Entrada amigable: dirección + actividad bastan; el resto es opcional."""

    model_config = ConfigDict(
        extra="ignore",
        allow_inf_nan=False,
        json_schema_extra={
            "examples": [
                {"activity": "Cafetería", "address": "Corrientes 2500"},
                {"rubro": "Cafetería", "direccion": "Corrientes 2500"},
            ]
        },
    )
    query: str | None = Field(default=None, max_length=4000)
    activity: str | None = Field(default=None, max_length=200)
    activity_code: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=250)
    confirm_activity: bool = False
    include_geometry: bool = False
    surface_m2: float | None = Field(default=None, gt=0)
    street_width_m: float | None = Field(default=None, gt=0)
    frontage_m: float | None = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def accept_common_frontend_names(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        aliases = {
            "activity": ("actividad", "rubro", "commercial_activity"),
            "address": ("direccion", "domicilio", "commercial_address"),
            "activity_code": ("codigo_actividad", "activityCode"),
            "query": ("consulta", "question"),
        }
        for canonical, alternatives in aliases.items():
            current = data.get(canonical)
            if canonical not in data or current is None or (isinstance(current, str) and not current.strip()):
                for alternative in alternatives:
                    candidate = data.get(alternative)
                    if candidate is not None and not (isinstance(candidate, str) and not candidate.strip()):
                        data[canonical] = candidate
                        break
        # Muchos formularios serializan controles opcionales vacíos como "".
        # Tratarlo como no informado evita 422 cuando actividad y dirección sí existen.
        for optional_number in ("surface_m2", "street_width_m", "frontage_m"):
            candidate = data.get(optional_number)
            if isinstance(candidate, str) and not candidate.strip():
                data[optional_number] = None
        for optional_bool in ("include_geometry", "confirm_activity"):
            candidate = data.get(optional_bool)
            if isinstance(candidate, str) and not candidate.strip():
                data[optional_bool] = False
        return data

    @field_validator("query", "activity", "activity_code", "address")
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
        info: ValidationInfo,
    ) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        # La ausencia se resuelve como estado funcional (needs_activity / needs_address),
        # no como un error HTTP por un campo vacío proveniente del formulario.
        return cleaned or None


class UrbanEvaluationRequest(RequestModel):
    activity: str = Field(min_length=2, max_length=200)
    address: str | None = Field(default=None, min_length=3, max_length=250)
    smp: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    surface_m2: float | None = Field(default=None, gt=0)
    street_width_m: float | None = Field(default=None, gt=0)
    frontage_m: float | None = Field(default=None, gt=0)

    @field_validator("activity")
    @classmethod
    def clean_activity(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("La actividad debe tener al menos 2 caracteres después de normalizar espacios.")
        return cleaned

    @field_validator("address", "smp")
    @classmethod
    def clean_optional_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if not cleaned:
            return None
        if info.field_name == "address" and len(cleaned) < 3:
            raise ValueError("La dirección debe tener al menos 3 caracteres después de normalizar espacios.")
        return cleaned


class QueryRequest(RequestModel):
    question: str = Field(
        min_length=5,
        max_length=4000,
    )
    activity: str = Field(
        min_length=2,
        max_length=200,
    )
    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=250,
    )
    surface_m2: float | None = Field(default=None, gt=0)
    street_width_m: float | None = Field(default=None, gt=0)
    frontage_m: float | None = Field(default=None, gt=0)
    retrieve_evidence: bool = False
    generate_answer: bool = False

    @field_validator("question", "activity")
    @classmethod
    def clean_required_text(cls, value: str, info: ValidationInfo) -> str:
        cleaned = " ".join(value.split())
        minimums = {"question": 5, "activity": 2}
        minimum = minimums[info.field_name]
        if len(cleaned) < minimum:
            raise ValueError(
                f"El campo debe tener al menos {minimum} caracteres después de normalizar espacios."
            )
        return cleaned

    @field_validator("address")
    @classmethod
    def clean_address(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if not cleaned:
            return None
        if len(cleaned) < 3:
            raise ValueError("La dirección debe tener al menos 3 caracteres después de normalizar espacios.")
        return cleaned


def _request_id(request: Request) -> uuid.UUID:
    return request.state.request_id


async def _source_versions_for_territory(request: Request, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Adjunta los metadatos disponibles sin asumir que toda tabla contextual existe."""
    source_ids: set[int] = set()
    parcel = data.get("parcel") or {}
    for key in ("source_version_id", "geometry_source_version_id"):
        if parcel.get(key) is not None:
            source_ids.add(int(parcel[key]))
    for rule in data.get("urban_rules") or []:
        if rule.get("source_version_id") is not None:
            source_ids.add(int(rule["source_version_id"]))
        source_ids.update(
            int(item["source_version_id"])
            for item in rule.get("special_districts", [])
            if item.get("source_version_id") is not None
        )
    for observation in data.get("land_use") or []:
        if observation.get("source_version_id") is not None:
            source_ids.add(int(observation["source_version_id"]))
    if not source_ids:
        return []
    return await request.app.state.source_repository.get_versions(source_ids)


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": settings.app_version,
    }


@router.get("/ready")
async def ready(request: Request) -> dict[str, Any]:
    pool = request.app.state.db_pool
    try:
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()
        capabilities = await request.app.state.territory_repository.schema_capabilities()
        # Core territorial data are required. Geometry, detailed procedures,
        # Anexo II mappings, and audit columns are reported as capabilities: a
        # missing optional table must not prevent the deterministic flow from
        # serving a useful partial response.
        core_ok = (
            capabilities.get("parcel_identity", {}).get("available", False)
            and capabilities.get("administrative_data", False)
            and capabilities.get("urban_rules", False)
        )
        if not core_ok:
            raise HTTPException(
                status_code=503,
                detail={"code": "database_core_schema_incompatible", "capabilities": capabilities},
            )
        optional_capabilities = (
            "geometry", "special_districts", "land_use", "activity_tramite_mappings",
            "procedure_detail_schema", "structured_query_audit",
        )
        degraded = [name for name in optional_capabilities if not capabilities.get(name)]
        return {
            "status": "ready",
            "degraded": bool(degraded),
            "degraded_capabilities": degraded,
            "schema_capabilities": capabilities,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database_unavailable") from exc


@router.post(
    "/geocoding",
    summary="Geocodificar una dirección (auxiliar)",
    description="Endpoint de diagnóstico/integración. El flujo principal ya incluye geocodificación.",
)
async def geocode(
    body: GeocodingRequest,
    request: Request,
) -> dict[str, Any]:
    try:
        service = request.app.state.geocoding_service

        result = await service.geocode(body.address)

        payload = result.to_dict()
        payload["usig_map_url"] = service.map_url(result)
        payload["request_id"] = str(_request_id(request))
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        source_ids = {int(result.source_version_id)} if result.source_version_id is not None else set()
        payload["sources"] = await request.app.state.source_repository.get_versions(source_ids) if source_ids else []
        payload["status"] = "resolved" if result.latitude is not None and result.longitude is not None else "partial"
        return payload

    except AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "ADDRESS_NOT_FOUND", "reason": str(exc)}) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "reason": str(exc)},
        ) from exc

    except USIGClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="geocoding_failed",
        ) from exc


@router.post(
    "/territory",
    summary="Resolver consulta territorial completa (determinista)",
    description=(
        "Endpoint principal del MVP: actividad + dirección → USIG → parcela/SMP → "
        "contexto territorial → compatibilidad → mapping/trámites → fuentes y advertencias. "
        "No invoca IA. Los estados parciales son resultados funcionales, no errores HTTP. "
        "La superficie, el ancho de calle, el frente y la geometría son opcionales."
    ),
    responses={
        404: {"model": ApiErrorResponse, "description": "USIG no pudo identificar la dirección ingresada."},
        422: {"model": ApiErrorResponse, "description": "Entrada inválida o dirección con formato no interpretable."},
        502: {"model": ApiErrorResponse, "description": "USIG u otro proveedor externo no está disponible."},
        503: {"model": ApiErrorResponse, "description": "La API o la base necesaria para procesar la consulta no está disponible."},
    },
)
async def resolve_territory_flow(
    body: TerritoryResolutionRequest,
    request: Request,
) -> dict[str, Any]:
    if not any((body.query, body.activity, body.activity_code, body.address)):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INPUT_REQUIRED",
                "reason": "Indicá al menos una actividad, un código de actividad, una dirección o una consulta.",
                "expected": ["activity", "activity_code", "address", "query"],
            },
        )
    # `activity` is the human-facing input. `activity_code` is optional; when both
    # are supplied the flow verifies that they refer to the same catalog record.
    # Do not reject the whole request at the HTTP layer.
    try:
        return await request.app.state.territory_flow_service.resolve(
            query=body.query,
            activity_input=body.activity,
            activity_code=body.activity_code,
            address_input=body.address,
            confirm_activity=body.confirm_activity,
            request_id=_request_id(request),
            include_geometry=body.include_geometry,
            surface_m2=body.surface_m2,
            street_width_m=body.street_width_m,
            frontage_m=body.frontage_m,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "ADDRESS_NOT_FOUND", "reason": str(exc)},
        ) from exc
    except USIGClientError as exc:
        raise HTTPException(status_code=502, detail="geocoding_provider_unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "reason": str(exc)}) from exc
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Territory flow failed request_id=%s", _request_id(request))
        raise HTTPException(status_code=503, detail="territory_resolution_unavailable") from exc


@router.get(
    "/territory",
    deprecated=True,
    summary="(Compatibilidad) Recuperar contexto por SMP/coordenadas",
    description="Para la consulta inicial del frontend, preferir POST /api/v1/territory.",
)
async def territory(
    request: Request,
    smp: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    include_geometry: bool = False,
) -> dict[str, Any]:
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=422, detail="latitude_and_longitude_must_be_provided_together")
    if not smp and latitude is None:
        raise HTTPException(status_code=422, detail="smp_or_coordinates_required")

    try:
        # SMP has priority if it resolves. Coordinates are still passed so they
        # can recover the parcel when the SMP is absent/invalid/not present in DB.
        data = await request.app.state.territory_service.resolve(
            {"smp": smp, "latitude": latitude, "longitude": longitude},
            include_geometry=include_geometry,
        )
        source_ids = set()
        parcel = data.get("parcel") or {}
        for key in ("source_version_id", "geometry_source_version_id"):
            if parcel.get(key) is not None:
                source_ids.add(int(parcel[key]))
        for rule in data.get("urban_rules") or []:
            if rule.get("source_version_id") is not None:
                source_ids.add(int(rule["source_version_id"]))
            source_ids.update(
                int(item["source_version_id"]) for item in rule.get("special_districts", [])
                if item.get("source_version_id") is not None
            )
        source_ids.update(
            int(item["source_version_id"]) for item in data.get("land_use", [])
            if item.get("source_version_id") is not None
        )
        data["sources"] = await request.app.state.source_repository.get_versions(source_ids) if source_ids else []
        data["request_id"] = str(_request_id(request))
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        data["resolution_status"] = data.get("resolution_status", "not_resolved")
        matched_parcel = data.get("parcel") or {}
        data["status"] = (
            "resolved"
            if data["resolution_status"] == "resolved"
            and matched_parcel.get("match_method") != "postgis_nearest_within_threshold"
            else "partial"
        )
        return data
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/territory/postgis-check", include_in_schema=False)
async def postgis_check(
    request: Request,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> dict[str, Any]:
    if settings.app_env == "production":
        raise HTTPException(
            status_code=404,
            detail="not_found",
        )

    repository = request.app.state.territory_repository

    return await repository.postgis_point_check(
        latitude=latitude,
        longitude=longitude,
    )



@router.post(
    "/territory/evaluate",
    deprecated=True,
    summary="(Compatibilidad) Evaluar actividad sobre un localizador ya disponible",
    description="Para el flujo completo nuevo, preferir POST /api/v1/territory.",
)
async def evaluate_territory_use(
    body: UrbanEvaluationRequest,
    request: Request,
) -> dict[str, Any]:
    if (body.latitude is None) != (body.longitude is None):
        raise HTTPException(status_code=422, detail="latitude_and_longitude_must_be_provided_together")
    has_coordinates = body.latitude is not None and body.longitude is not None
    locator_count = int(bool(body.address)) + int(bool(body.smp)) + int(has_coordinates)
    if locator_count != 1:
        raise HTTPException(status_code=422, detail="provide_exactly_one_locator_address_smp_or_coordinates")

    service = request.app.state.urban_evaluation_service
    try:
        if body.address:
            location = await request.app.state.geocoding_service.geocode(body.address)
            territory_data = await request.app.state.territory_service.resolve(location, include_geometry=False)
        else:
            location = None
            territory_data = await request.app.state.territory_service.resolve(
                {"smp": body.smp, "latitude": body.latitude, "longitude": body.longitude},
                include_geometry=False,
            )
        urban_rule = (territory_data.get("urban_rules") or [None])[0]
        result = await service.evaluate(
            body.activity, urban_rule, surface_m2=body.surface_m2,
            street_width_m=body.street_width_m, frontage_m=body.frontage_m,
        )
    except AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "ADDRESS_NOT_FOUND", "reason": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "reason": str(exc)}) from exc
    except USIGClientError as exc:
        raise HTTPException(status_code=502, detail="geocoding_provider_unavailable") from exc

    source_ids = set()
    if location and location.source_version_id is not None:
        source_ids.add(int(location.source_version_id))
    parcel = territory_data.get("parcel") or {}
    for key in ("source_version_id", "geometry_source_version_id"):
        if parcel.get(key) is not None:
            source_ids.add(int(parcel[key]))
    if urban_rule and urban_rule.get("source_version_id") is not None:
        source_ids.add(int(urban_rule["source_version_id"]))
    source_ids.update(
        int(item["source_version_id"]) for item in (urban_rule or {}).get("special_districts", [])
        if item.get("source_version_id") is not None
    )
    source_ids.update(
        int(item["source_version_id"]) for item in result.get("evaluations", [])
        if item.get("source_version_id") is not None
    )
    result["request_id"] = str(_request_id(request))
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["input"] = {
        "activity": body.activity, "address": body.address, "smp": body.smp,
        "latitude": body.latitude, "longitude": body.longitude,
        "surface_m2": body.surface_m2, "street_width_m": body.street_width_m,
        "frontage_m": body.frontage_m,
    }
    result["location"] = ({
        "address_input": location.input_address, "address_normalized": location.normalized_address,
        "latitude": location.latitude, "longitude": location.longitude, "smp": location.smp,
        "source_version_id": location.source_version_id, "warnings": location.warnings,
    } if location else None)
    result["territory"] = territory_data
    result["sources"] = await request.app.state.source_repository.get_versions(source_ids) if source_ids else []
    result["warnings"] = list(dict.fromkeys(territory_data.get("warnings", []) + (location.warnings if location else [])))
    return result

@router.post(
    "/queries",
    response_model=QueryResponse,
    summary="Consulta heredada con recuperación/IA opcional",
    description="No utilizar como endpoint principal del MVP determinista; ver POST /api/v1/territory.",
)
async def query(
    body: QueryRequest,
    request: Request,
) -> dict[str, Any]:
    if len(body.question) > settings.max_request_chars:
        raise HTTPException(
            status_code=413,
            detail="request_too_large",
        )

    try:
        return await request.app.state.query_service.execute(
            body.question,
            body.activity,
            body.address,
            body.retrieve_evidence,
            body.generate_answer,
            _request_id(request),
            body.surface_m2,
            body.street_width_m,
            body.frontage_m,
        )

    except AddressNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "ADDRESS_NOT_FOUND", "reason": str(exc)}) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "reason": str(exc)},
        ) from exc

    except RuntimeError as exc:
        if str(exc) == "query_capacity_exhausted":
            raise HTTPException(
                status_code=429,
                detail="query_capacity_exhausted",
            ) from exc

        if str(exc) == "query_unavailable":
            raise HTTPException(
                status_code=503,
                detail="query_unavailable",
            ) from exc

        raise

    except USIGClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="geocoding_failed",
        ) from exc

    except OllamaClientError as exc:
        raise HTTPException(
            status_code=502,
            detail="ai_service_unavailable",
        ) from exc

@router.get("/map/parcel/{smp}")
async def map_parcel(smp: str, request: Request) -> dict[str, Any]:
    """Devuelve un GeoJSON Feature solo si hay geometría de parcela disponible."""
    try:
        data = await request.app.state.territory_service.resolve({"smp": smp}, include_geometry=True)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Map parcel failed request_id=%s", _request_id(request))
        raise HTTPException(status_code=503, detail="map_data_unavailable") from exc
    parcel = data.get("parcel")
    if not parcel:
        raise HTTPException(status_code=404, detail={"code": "parcel_not_found", "smp": smp, "warnings": data.get("warnings", [])})
    sources = await _source_versions_for_territory(request, data)
    geometry = parcel.get("geometry")
    if not geometry:
        return {
            "type": "Feature", "id": parcel.get("id"), "geometry": None,
            "properties": {
                "smp": parcel.get("smp"), "geometry_status": parcel.get("geometry_status", "unavailable"),
                "source_version_id": parcel.get("source_version_id"),
                "geometry_source_version_id": parcel.get("geometry_source_version_id"),
                "warnings": data.get("warnings", []),
            },
            "status": "partial",
            "warnings": data.get("warnings", []),
            "request_id": str(_request_id(request)),
            "sources": sources,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    urban_rule = (data.get("urban_rules") or [None])[0] or {}
    return {
        "type": "Feature", "id": parcel.get("id"), "geometry": geometry,
        "properties": {
            "smp": parcel.get("smp"), "partida_ma": parcel.get("partida_ma"),
            "barrio": parcel.get("barrio"), "comuna": parcel.get("comuna"),
            "mixturas": urban_rule.get("mixturas", []),
            "special_districts": urban_rule.get("special_districts", []),
            "indicators": {key: urban_rule.get(key) for key in ("sm", "catalogado", "rh", "ensanche", "apertura", "lep", "ci_digital", "anac") if urban_rule.get(key) is not None},
            "source_version_id": parcel.get("source_version_id"),
            "geometry_source_version_id": parcel.get("geometry_source_version_id"),
            "resolution_method": parcel.get("match_method"),
        },
        "status": "resolved",
        "warnings": data.get("warnings", []),
        "request_id": str(_request_id(request)),
        "sources": sources,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/context/parcel/{smp}")
async def parcel_context(smp: str, request: Request) -> dict[str, Any]:
    """Contexto territorial consultable sin geocodificar otra vez una dirección."""
    try:
        data = await request.app.state.territory_service.resolve({"smp": smp}, include_geometry=False)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Parcel context failed request_id=%s", _request_id(request))
        raise HTTPException(status_code=503, detail="territory_context_unavailable") from exc
    if not data.get("parcel"):
        raise HTTPException(status_code=404, detail={"code": "parcel_not_found", "smp": smp, "warnings": data.get("warnings", [])})
    parcel = data["parcel"]
    urban_rule = (data.get("urban_rules") or [None])[0]
    sources = await _source_versions_for_territory(request, data)
    return {
        "smp": parcel.get("smp"),
        "parcel": {
            **{k: parcel.get(k) for k in ("id", "smp", "partida_ma", "source_version_id", "geometry_source_version_id", "match_method", "match_distance_m")},
            "confirmation_required": parcel.get("match_method") == "postgis_nearest_within_threshold",
        },
        "administrative": {
            "barrio": {"id": parcel.get("barrio_id"), "name": parcel.get("barrio")} if parcel.get("barrio") else None,
            "comuna": {"id": parcel.get("comuna_id"), "name": parcel.get("comuna")} if parcel.get("comuna") else None,
        },
        "urbanism": {
            "status": "available" if urban_rule else "unavailable",
            "mixturas": (urban_rule or {}).get("mixturas", []),
            "special_districts": (urban_rule or {}).get("special_districts", []),
            "indicators": {k: (urban_rule or {}).get(k) for k in ("sm", "catalogado", "rh", "ensanche", "apertura", "lep", "ci_digital", "anac") if (urban_rule or {}).get(k) is not None},
            "source_version_id": (urban_rule or {}).get("source_version_id"),
        },
        "land_use": data.get("land_use", []),
        "resolution_status": data.get("resolution_status", "not_resolved"),
        "status": (
            "resolved"
            if urban_rule and data.get("resolution_status") == "resolved"
            and parcel.get("match_method") != "postgis_nearest_within_threshold"
            else "partial"
        ),
        "warnings": data.get("warnings", []),
        "request_id": str(_request_id(request)),
        "sources": sources,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }



@router.get("/activities")
async def search_activities(
    request: Request,
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Catálogo/autocomplete oficial para selección explícita del rubro en el Frontend."""
    if search is not None:
        search = " ".join(search.split()) or None
    result = await request.app.state.activity_repository.search_catalog(search, limit=limit, offset=offset)
    source_ids = {
        int(item["source_version_id"]) for item in result["items"]
        if item.get("source_version_id") is not None
    }
    result["sources"] = await request.app.state.source_repository.get_versions(source_ids) if source_ids else []
    result["status"] = "available" if result["items"] else "empty"
    result["request_id"] = str(_request_id(request))
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    return result


@router.get("/activities/{activity_id}/procedures")
async def activity_procedures(activity_id: int, request: Request) -> dict[str, Any]:
    if activity_id < 1:
        raise HTTPException(status_code=422, detail="invalid_activity_id")
    flow = request.app.state.territory_flow_service
    try:
        mapping, procedures = await flow._load_procedures(activity_id)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Activity procedures failed request_id=%s", _request_id(request))
        raise HTTPException(status_code=503, detail="procedure_data_unavailable") from exc
    source_ids = set()
    if mapping.get("source_version_id") is not None:
        source_ids.add(int(mapping["source_version_id"]))
    for procedure in procedures:
        if procedure.get("source_version_id") is not None:
            source_ids.add(int(procedure["source_version_id"]))
        if procedure.get("procedure_source_version_id") is not None:
            source_ids.add(int(procedure["procedure_source_version_id"]))
        for collection_name in ("requisitos", "documentos", "pasos", "reglas", "variantes"):
            for item in procedure.get(collection_name) or []:
                if item.get("source_version_id") is not None:
                    source_ids.add(int(item["source_version_id"]))
    sources = await request.app.state.source_repository.get_versions(source_ids) if source_ids else []
    complete = bool(procedures) and all(
        item.get("detail_schema_status", "available") == "available"
        and any(item.get(key) for key in ("requisitos", "documentos", "pasos", "reglas"))
        for item in procedures
    )
    detail_status = "available" if complete else ("partial" if procedures else "not_loaded")
    warnings = list(mapping.get("warnings", []))
    warnings.extend(warning for item in procedures for warning in item.get("detail_warnings", []))
    if not procedures:
        warnings.append("PROCEDURE_DETAILS_NOT_LOADED")
    elif not complete:
        warnings.append("PROCEDURE_CONTENT_INCOMPLETE")
    return {
        "activity_id": activity_id,
        "procedure_type_mapping": mapping,
        "procedure_details_status": detail_status,
        "procedures": procedures,
        "sources": sources,
        "request_id": str(_request_id(request)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": list(dict.fromkeys(warnings)),
    }
