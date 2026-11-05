"""Punto de entrada FastAPI y composición de dependencias compartidas por proceso."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api.routes import router
from app.core.config import settings
from app.core.database import async_pool, close_pool, open_pool
from app.core.logging import configure_logging
from app.integrations.ollama import OllamaClient
from app.integrations.usig import USIGClient
from app.services.geocoding import GeocodingService
from app.services.query import QueryService
from app.repositories.activity import ActivityRepository
from app.repositories.activity_tramite_mappings import ActivityTramiteMappingRepository
from app.repositories.sources import SourceRepository
from app.repositories.queries import QueryRepository
from app.services.procedures import ProcedureService
from app.services.input_interpreter import InputInterpreterService
from app.services.territory_flow import TerritoryFlowService
from app.repositories.territory import TerritoryRepository
from app.repositories.urban_uses import UrbanUseRuleRepository
from app.services.territory import TerritoryService
from app.services.urban_evaluation import UrbanEvaluationService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)

    usig: USIGClient | None = None
    ollama: OllamaClient | None = None

    try:
        # Database
        await open_pool()
        app.state.db_pool = async_pool()

        # External clients
        usig = USIGClient(
            settings.usig_rest_url,
            settings.usig_root_url,
            settings.usig_geocoder_url,
            timeout=settings.usig_timeout_seconds,
            max_retries=settings.usig_max_retries,
            max_concurrency=settings.usig_max_concurrency,
        )

        ollama = OllamaClient(
            settings.ollama_base_url,
            settings.ollama_chat_model,
            settings.ollama_embed_model,
            chat_timeout=settings.ollama_chat_timeout_seconds,
            embed_timeout=settings.ollama_embed_timeout_seconds,
            max_retries=settings.ollama_max_retries,
            chat_max_concurrency=settings.ollama_chat_max_concurrency,
            embed_max_concurrency=settings.ollama_embed_max_concurrency,
        )

        # Application services
        app.state.usig = usig
        app.state.ollama = ollama

        app.state.geocoding_service = GeocodingService(
            usig,
        )

        territory_repository = TerritoryRepository(app.state.db_pool)
        territory_service = TerritoryService(
            territory_repository,
            geometry_source_path=settings.parcel_geometry_source_path,
            geometry_source_layer=settings.parcel_geometry_source_layer,
            geometry_source_version_id=settings.parcel_geometry_source_version_id,
            cache_geometry_on_resolve=settings.parcel_geometry_cache_on_resolve,
        )
        urban_use_rule_repository = UrbanUseRuleRepository(app.state.db_pool)

        activity_repository = ActivityRepository()
        urban_evaluation_service = UrbanEvaluationService(
            activity_repository,
            urban_use_rule_repository,
        )

        app.state.territory_repository = territory_repository
        app.state.activity_repository = activity_repository
        app.state.territory_service = territory_service
        app.state.urban_evaluation_service = urban_evaluation_service
        source_repository = SourceRepository()
        app.state.source_repository = source_repository
        app.state.territory_flow_service = TerritoryFlowService(
            app.state.geocoding_service,
            territory_service,
            urban_evaluation_service,
            activities=activity_repository,
            mappings=ActivityTramiteMappingRepository(),
            procedures=ProcedureService(),
            sources=source_repository,
            queries=QueryRepository(),
            input_interpreter=InputInterpreterService(ollama),
            input_interpreter_enabled=settings.ai_input_interpreter_enabled,
            input_interpreter_timeout_seconds=settings.ai_input_interpreter_timeout_seconds,
        )

        app.state.query_service = QueryService(
            app.state.geocoding_service,
            ollama,
            territory_service,
            urban_evaluation_service,
        )

        yield

    finally:
        if ollama is not None:
            await ollama.close()

        if usig is not None:
            await usig.close()

        await close_pool()


app = FastAPI(
    title=settings.project_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)


def _error_payload(request: Request, code: str, message: str, details=None) -> dict:
    request_id = getattr(getattr(request, "state", None), "request_id", None)
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": str(request_id) if request_id else None,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    # Preserve the safe, stable reason from explicit HTTPException responses too.
    # Previously string details were discarded, leaving a generic 422/503 that
    # was difficult to debug from Swagger or the Frontend.
    details = detail if isinstance(detail, (dict, list)) else ({"reason": detail} if isinstance(detail, str) and exc.status_code < 500 else None)
    detail_code = detail.get("code") if isinstance(detail, dict) else None
    if detail_code:
        code = str(detail_code).upper()
    else:
        code = {
            400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
            404: "NOT_FOUND", 409: "CONFLICT", 413: "REQUEST_TOO_LARGE",
            422: "VALIDATION_ERROR", 429: "RATE_LIMITED", 502: "UPSTREAM_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }.get(exc.status_code, "HTTP_ERROR")
    message = {
        "BAD_REQUEST": "La solicitud no es válida.",
        "INPUT_REQUIRED": "Falta información para iniciar la consulta.",
        "NOT_FOUND": "No se encontró el recurso solicitado.",
        "VALIDATION_ERROR": "Hay campos faltantes o inválidos en la solicitud.",
        "INVALID_INPUT": "No pudimos interpretar alguno de los datos ingresados.",
        "ADDRESS_NOT_FOUND": "No se encontró la dirección en el servicio de normalización.",
        "REQUEST_TOO_LARGE": "La solicitud supera el tamaño permitido.",
        "RATE_LIMITED": "El servicio está ocupado; reintentá más tarde.",
        "UPSTREAM_ERROR": "Un servicio externo no pudo completar la operación.",
        "SERVICE_UNAVAILABLE": "El servicio no está disponible temporalmente.",
        "DATABASE_SCHEMA_INCOMPATIBLE": "La base de datos no tiene el esquema requerido.",
    }.get(code, "No pudimos completar la solicitud.")
    return JSONResponse(status_code=exc.status_code, content=_error_payload(request, code, message, details))


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    # No devolver el valor input, para no replicar direcciones ni otros datos ingresados.
    errors = [
        {
            "location": list(item.get("loc", ())),
            "type": item.get("type"),
            "message": item.get("msg"),
            "hint": (
                "El cuerpo no es JSON válido. Revisá comillas, llaves y comas; JSON no admite coma final."
                if item.get("type") == "json_invalid"
                else "El campo es obligatorio o falta en el cuerpo de la solicitud."
                if item.get("type") == "missing"
                else "El campo no está definido en este endpoint. Revisá los nombres admitidos en /docs."
                if item.get("type") == "extra_forbidden"
                else "Revisá el tipo, formato y restricciones del campo indicado."
            ),
        }
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_payload(request, "VALIDATION_ERROR", "Hay campos faltantes o inválidos en la solicitud.", {"fields": errors}),
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception request_id=%s", getattr(request.state, "request_id", None))
    return JSONResponse(
        status_code=500,
        content=_error_payload(request, "INTERNAL_ERROR", "No pudimos completar la solicitud."),
    )


allowed_hosts = settings.allowed_host_list()

if allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time-ms",
    ],
)


@app.middleware("http")
async def security_and_request_context(
    request: Request,
    call_next,
) -> Response:
    raw_id = request.headers.get("x-request-id")

    try:
        request_id = (
            uuid.UUID(raw_id)
            if raw_id
            else uuid.uuid4()
        )
    except ValueError:
        return JSONResponse(
            content={"error": {"code": "INVALID_REQUEST_ID", "message": "El encabezado X-Request-ID debe ser un UUID válido.", "request_id": None}},
            status_code=400,
        )

    request.state.request_id = request_id

    start = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = (
        time.perf_counter() - start
    ) * 1000

    logger.info(
        "http method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )

    response.headers["X-Request-ID"] = str(request_id)
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.1f}"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    return response


app.include_router(router)