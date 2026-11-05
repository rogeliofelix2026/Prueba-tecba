"""Caso de uso principal: actividad + ubicación + territorio + trámites + evidencia + IA."""

import asyncio
import logging
import uuid

from app.api.query_context import (
    Actividad,
    Consulta,
    Procedimiento,
    QueryContext,
    QueryResponse,
    Territorio,
    Ubicacion,
)
from app.core.config import settings
from app.integrations.ollama import OllamaClient, OllamaClientError
from app.integrations.usig import USIGClient, USIGClientError
from app.rag.service import RagService
from app.repositories.activity import ActivityRepository
from app.repositories.activity_tramite_mappings import ActivityTramiteMappingRepository
from app.repositories.ai_model import AIModelRepository
from app.repositories.queries import QueryRepository
from app.repositories.sources import SourceRepository
from app.services.geocoding import GeocodingService
from app.services.procedures import ProcedureService
from app.services.territory import TerritoryService
from app.services.urban_evaluation import UrbanEvaluationService

logger = logging.getLogger(__name__)


class QueryService:
    """Servicio reutilizable por proceso; conserva backpressure y single-flight de geocoding."""

    def __init__(
        self,
        geocoding: GeocodingService,
        ollama: OllamaClient,
        territory: TerritoryService,
        urban_evaluation: UrbanEvaluationService,
    ) -> None:
        self.activity = ActivityRepository()
        self.geo = geocoding
        self.territory = territory
        self.urban_evaluation = urban_evaluation
        self.procedure = ProcedureService()
        self.activity_tramite_mappings = ActivityTramiteMappingRepository()
        self.rag = RagService(ollama)
        self.queries = QueryRepository()
        self.models = AIModelRepository()
        self.sources = SourceRepository()
        self._query_slots = asyncio.Semaphore(settings.query_max_concurrency)

    async def execute(
        self,
        question: str,
        activity_input: str,
        address: str | None,
        retrieve_evidence: bool,
        generate_answer: bool,
        request_id: uuid.UUID,
        surface_m2: float | None = None,
        street_width_m: float | None = None,
        frontage_m: float | None = None,
    ) -> dict:
        try:
            await asyncio.wait_for(
                self._query_slots.acquire(), timeout=settings.query_queue_timeout_seconds
            )
        except TimeoutError as exc:
            raise RuntimeError("query_capacity_exhausted") from exc

        try:
            return await self._execute_inner(
                question, activity_input, address, retrieve_evidence, generate_answer, request_id,
                surface_m2, street_width_m, frontage_m
            )
        finally:
            self._query_slots.release()

    async def _execute_inner(
        self,
        question: str,
        activity_input: str,
        address: str | None,
        retrieve_evidence: bool,
        generate_answer: bool,
        request_id: uuid.UUID,
        surface_m2: float | None,
        street_width_m: float | None,
        frontage_m: float | None,
    ) -> dict:
        tasks = {"activity": asyncio.create_task(self.activity.resolve(activity_input))}
        if generate_answer:
            tasks["chat_model"] = asyncio.create_task(
                self.models.id_for("ollama", settings.ollama_chat_model, "chat")
            )
        if retrieve_evidence:
            tasks["embedding_model"] = asyncio.create_task(
                self.models.id_for("ollama", settings.ollama_embed_model, "embedding")
            )

        try:
            results = await asyncio.gather(*tasks.values())
        except BaseException:
            for task in tasks.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks.values(), return_exceptions=True)
            raise

        result_map = dict(zip(tasks, results, strict=True))
        activity = result_map["activity"]
        chat_model_id = result_map.get("chat_model")
        embedding_model_id = result_map.get("embedding_model")
        query_id = await self.queries.start(
            request_id, question, activity_input, address, chat_model_id, embedding_model_id,
            request_payload={
                "question": question, "activity": activity_input, "address": address,
                "surface_m2": surface_m2, "street_width_m": street_width_m, "frontage_m": frontage_m,
                "retrieve_evidence": retrieve_evidence, "generate_answer": generate_answer,
            },
            execution_mode="ai_assisted" if (retrieve_evidence or generate_answer) else "legacy",
        )

        try:
            if activity is None:
                raise ValueError("Actividad no encontrada en el catálogo.")

            if address:
                location, procedures, tramite_mapping = await asyncio.gather(
                    self.geo.geocode(address),
                    self.procedure.resolve(activity["id"]),
                    self.activity_tramite_mappings.for_activity(activity["id"]),
                )
            else:
                location = None
                procedures, tramite_mapping = await asyncio.gather(
                    self.procedure.resolve(activity["id"]),
                    self.activity_tramite_mappings.for_activity(activity["id"]),
                )

            territory = await self.territory.resolve(location, include_geometry=False)

            await self.queries.update_context(
                query_id,
                activity["id"],
                location.normalized_address if location else None,
                location.street_code if location else None,
                location.latitude if location else None,
                location.longitude if location else None,
                surface_m2,
                street_width_m,
                frontage_m,
                territory.get("parcel", {}).get("id") if territory.get("parcel") else None,
            )

            evidence = (
                await self.rag.retrieve(question, embedding_model_id, activity["code"])
                if retrieve_evidence
                else []
            )

            compatibility = await self.urban_evaluation.evaluate(
                activity["name"],
                territory.get("urban_rules", [None])[0] if territory.get("urban_rules") else None,
                surface_m2=surface_m2,
                street_width_m=street_width_m,
                frontage_m=frontage_m,
            )

            context = self._build_context(
                question, activity_input, address, activity, location, territory, procedures, compatibility,
                tramite_mapping,
            )

            source_ids = self._collect_source_version_ids(context, evidence)
            sources = await self.sources.get_versions(source_ids)
            context = context.model_copy(update={"fuentes": sources})

            answer = (
                await self.rag.generate(question, context.model_dump(mode="json"), evidence)
                if generate_answer
                else None
            )

            await self.queries.add_evidence(query_id, evidence)
            await self.queries.add_urban_rule_evidence(
                query_id,
                territory.get("urban_rules", [{}])[0].get("id")
                if territory.get("urban_rules")
                else None,
            )
            await self.queries.add_activity_rule_evidence(
                query_id,
                [
                    item["activity_use_rule_id"]
                    for item in compatibility.get("evaluations", [])
                    if item.get("activity_use_rule_id") is not None
                ],
            )
            await self.queries.add_source_evidence(query_id, source_ids)

            partial = bool(
                (location and location.warnings)
                or not procedures
                or compatibility.get("status") == "insufficient_data"
                or tramite_mapping.get("status") != "confirmed"
            )
            response = QueryResponse(
                query_id=str(query_id),
                status="partial" if partial else "completed",
                answer=answer,
                context=context,
                evidence=evidence,
                links={"usig_map": self.geo.map_url(location) if location else None},
            )
            response_payload = response.model_dump(mode="json")
            await self.queries.complete(
                query_id, answer, partial=partial, response_json=response_payload,
                execution_mode="ai_assisted" if (retrieve_evidence or generate_answer) else "legacy",
            )
            return response_payload
        except ValueError as exc:
            await self._safe_fail(query_id, "validation_error", str(exc))
            raise
        except OllamaClientError:
            await self._safe_fail(query_id, "ollama_unavailable")
            raise
        except USIGClientError:
            await self._safe_fail(query_id, "usig_unavailable")
            raise
        except asyncio.CancelledError:
            await self._safe_fail(query_id, "request_cancelled")
            raise
        except Exception as exc:
            logger.exception("Query falló query_id=%s request_id=%s", query_id, request_id)
            await self._safe_fail(query_id, "query_failed")
            raise RuntimeError("query_unavailable") from exc

    @staticmethod
    def _build_context(
        question: str,
        activity_input: str,
        address: str | None,
        activity: dict,
        location,
        territory: dict,
        procedures: list[dict],
        compatibility: dict,
        tramite_mapping: dict,
    ) -> QueryContext:
        return QueryContext(
            consulta=Consulta(
                texto_original=question,
                actividad_original=activity_input,
                direccion_original=address,
            ),
            actividad=Actividad(
                id=activity["id"],
                codigo=activity["code"],
                nombre=activity["name"],
                categoria=activity.get("category"),
                estado_mapeo=activity.get("mapping_status"),
                source_version_id=activity.get("source_version_id"),
                alias_source_version_id=activity.get("alias_source_version_id"),
            ),
            ubicacion=(
                Ubicacion(
                    direccion_original=location.input_address,
                    direccion_normalizada=location.normalized_address,
                    latitud=location.latitude,
                    longitud=location.longitude,
                    smp=location.smp,
                    codigo_calle=location.street_code,
                    altura=location.height,
                    advertencias=location.warnings,
                    desde_cache=location.from_cache,
                    source_version_id=location.source_version_id,
                )
                if location
                else None
            ),
            territorio=Territorio(
                parcela=territory.get("parcel"),
                reglas_urbanisticas=territory.get("urban_rules", []),
                usos_suelo=territory.get("land_use", []),
                compatibilidad_urbanistica=compatibility,
            ),
            procedimientos=[Procedimiento(**item) for item in procedures],
            clasificacion_tramite=tramite_mapping,
        )

    @staticmethod
    def _collect_source_version_ids(context: QueryContext, evidence: list[dict]) -> set[int]:
        ids: set[int] = set()
        if context.ubicacion and context.ubicacion.source_version_id is not None:
            ids.add(context.ubicacion.source_version_id)
        if context.actividad.source_version_id is not None:
            ids.add(context.actividad.source_version_id)
        if context.actividad.alias_source_version_id is not None:
            ids.add(context.actividad.alias_source_version_id)
        if context.clasificacion_tramite and context.clasificacion_tramite.get("source_version_id") is not None:
            ids.add(int(context.clasificacion_tramite["source_version_id"]))
        for item in context.territorio.reglas_urbanisticas + context.territorio.usos_suelo:
            value = item.get("source_version_id")
            if value is not None:
                ids.add(int(value))
        if context.territorio.parcela:
            value = context.territorio.parcela.get("source_version_id")
            if value is not None:
                ids.add(int(value))
        for procedure in context.procedimientos:
            if procedure.source_version_id is not None:
                ids.add(procedure.source_version_id)
            for collection in (
                procedure.requisitos,
                procedure.documentos,
                procedure.pasos,
                procedure.reglas,
            ):
                for item in collection:
                    value = item.get("source_version_id")
                    if value is not None:
                        ids.add(int(value))
        for item in evidence:
            value = item.get("source_version_id")
            if value is not None:
                ids.add(int(value))
        return ids

    async def _safe_fail(
        self, query_id: uuid.UUID, error_code: str, message: str | None = None
    ) -> None:
        try:
            await self.queries.fail(query_id, error_code, message)
        except Exception:
            logger.exception("No se pudo registrar el fallo de query_id=%s", query_id)
