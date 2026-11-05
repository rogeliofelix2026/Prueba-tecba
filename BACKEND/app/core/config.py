"""Configuración central del backend mediante variables de entorno."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Sistema de Gestión Inteligente"
    app_env: str = "local"
    app_name: str = "gestion-inteligente-api"
    app_version: str = "0.3.7"
    log_level: str = "INFO"

    # Database
    database_url: str | None = None
    db_min_size: int = 1
    db_max_size: int = 5
    db_timeout_seconds: float = 5.0

    # USIG
    usig_rest_url: str = "https://ws.usig.buenosaires.gob.ar/rest"
    usig_root_url: str = "https://ws.usig.buenosaires.gob.ar"
    usig_geocoder_url: str = "https://ws.usig.buenosaires.gob.ar/geocoder/2.2"
    usig_timeout_seconds: float = 10.0
    usig_max_retries: int = 2
    usig_max_concurrency: int = 8
    usig_cache_ttl_hours: int = 24
    usig_partial_cache_ttl_hours: int = 1

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embed_model: str = "bge-m3"
    ollama_chat_timeout_seconds: float = 120.0
    # La extracción inicial debe fallar rápido para conservar el flujo determinístico.
    ai_input_interpreter_timeout_seconds: float = 12.0
    ollama_embed_timeout_seconds: float = 120.0
    ollama_max_retries: int = 2
    ollama_chat_max_concurrency: int = 2
    ollama_embed_max_concurrency: int = 2

    # Embeddings
    embedding_dimension: int = 1024

    # RAG
    rag_enabled: bool = False
    # Dos etapas de IA independientes; ambas desactivadas por defecto.
    ai_input_interpreter_enabled: bool = False
    ai_explanation_enabled: bool = False
    rag_top_k: int = 8
    rag_candidate_multiplier: int = 4
    rag_vector_weight: float = 0.75
    rag_lexical_weight: float = 0.25
    rag_max_chunk_chars: int = 2500
    rag_max_context_chars: int = 10000

    # Request limits
    max_request_chars: int = 4000

    # Territory
    territory_land_use_limit: int = 20
    # Fuente oficial de polígonos catastrales local/montada. USIG geocodifica y
    # devuelve SMP; no se asume que exponga polígonos con el endpoint /smp.
    parcel_geometry_source_path: str | None = None
    parcel_geometry_source_layer: str | None = None
    # Debe apuntar a source_versions.id de sources.code='parcelas' correspondiente
    # al mismo fichero montado. El servicio no cachea geometría sin esa procedencia explícita.
    parcel_geometry_source_version_id: int | None = None
    parcel_geometry_cache_on_resolve: bool = True

    # Query concurrency
    query_max_concurrency: int = 4
    query_queue_timeout_seconds: float = 2.0

    # HTTP / security
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000"
    )
    allowed_hosts: str = ""

    # Documentation
    # Fail closed: la documentación interactiva solo se habilita explícitamente.
    docs_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "db_min_size",
        "db_max_size",
        "usig_max_concurrency",
        "ollama_chat_max_concurrency",
        "ollama_embed_max_concurrency",
        "embedding_dimension",
        "rag_top_k",
        "rag_candidate_multiplier",
        "rag_max_chunk_chars",
        "rag_max_context_chars",
        "max_request_chars",
        "territory_land_use_limit",
        "query_max_concurrency",
    )
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value < 1:
            raise ValueError("debe ser mayor que 0")
        return value

    @field_validator(
        "db_timeout_seconds",
        "usig_timeout_seconds",
        "ollama_chat_timeout_seconds",
        "ai_input_interpreter_timeout_seconds",
        "ollama_embed_timeout_seconds",
        "query_queue_timeout_seconds",
    )
    @classmethod
    def validate_positive_floats(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("debe ser mayor que 0")
        return value

    @model_validator(mode="after")
    def validate_cross_field_constraints(self) -> "Settings":
        if self.db_max_size < self.db_min_size:
            raise ValueError(
                "db_max_size debe ser >= db_min_size"
            )

        if self.rag_vector_weight < 0 or self.rag_lexical_weight < 0:
            raise ValueError(
                "Los pesos de RAG no pueden ser negativos."
            )

        if (
            self.rag_vector_weight == 0
            and self.rag_lexical_weight == 0
        ):
            raise ValueError(
                "Al menos un peso de RAG debe ser mayor que 0."
            )

        return self

    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def allowed_host_list(self) -> list[str]:
        return [
            host.strip()
            for host in self.allowed_hosts.split(",")
            if host.strip()
        ]

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError(
                "DATABASE_URL no está configurada."
            )

        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()