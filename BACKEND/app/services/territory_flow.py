"""Orquestación determinista de la consulta inicial del vertical slice territorial."""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from app.repositories.activity import ActivityRepository
from app.repositories.activity_tramite_mappings import ActivityTramiteMappingRepository
from app.repositories.sources import SourceRepository
from app.repositories.queries import QueryRepository
from app.services.geocoding import GeocodingService
from app.services.initial_query import build_request_context, extract_address
from app.services.input_interpreter import InputInterpreterError, InputInterpreterService
from app.services.procedures import ProcedureService
from app.services.territory import TerritoryService
from app.services.urban_evaluation import UrbanEvaluationService

logger = logging.getLogger(__name__)


def procedure_details_are_present(procedures: list[dict[str, Any]]) -> bool:
    """Permite que el flujo avance con algún detalle útil, aunque la ficha sea parcial."""
    return bool(procedures) and all(
        any(item.get(key) for key in ("requisitos", "documentos", "pasos", "reglas", "variantes"))
        for item in procedures
    )


def procedure_details_are_complete(procedures: list[dict[str, Any]]) -> bool:
    """Separa una ficha completa para la UI de una clasificación con detalles parciales."""
    return bool(procedures) and all(
        item.get("detail_schema_status", "available") == "available"
        and bool(item.get("requisitos"))
        and bool(item.get("documentos"))
        and bool(item.get("pasos"))
        for item in procedures
    )


class TerritoryFlowService:
    """Actividad confirmada + geocodificación USIG + reglas territoriales + trámites."""

    def __init__(
        self,
        geocoding: GeocodingService,
        territory: TerritoryService,
        urban_evaluation: UrbanEvaluationService,
        *,
        activities: ActivityRepository | None = None,
        mappings: ActivityTramiteMappingRepository | None = None,
        procedures: ProcedureService | None = None,
        sources: SourceRepository | None = None,
        queries: QueryRepository | None = None,
        input_interpreter: InputInterpreterService | None = None,
        input_interpreter_enabled: bool = False,
        input_interpreter_timeout_seconds: float = 12.0,
    ) -> None:
        self.geocoding = geocoding
        self.territory = territory
        self.urban_evaluation = urban_evaluation
        self.activities = activities or ActivityRepository()
        self.mappings = mappings or ActivityTramiteMappingRepository()
        self.procedures = procedures or ProcedureService()
        self.sources = sources or SourceRepository()
        self.queries = queries
        self.input_interpreter = input_interpreter
        self.input_interpreter_enabled = input_interpreter_enabled
        self.input_interpreter_timeout_seconds = max(0.1, float(input_interpreter_timeout_seconds))

    async def resolve(
        self,
        *,
        query: str | None,
        activity_input: str | None,
        activity_code: str | None,
        address_input: str | None,
        confirm_activity: bool,
        request_id: uuid.UUID,
        include_geometry: bool = False,
        surface_m2: float | None = None,
        street_width_m: float | None = None,
        frontage_m: float | None = None,
    ) -> dict[str, Any]:
        question = (query or "").strip()
        explicit_activity = (activity_input or "").strip()
        input_warnings: list[str] = []
        input_stage: dict[str, Any] = {
            "enabled": self.input_interpreter_enabled,
            "status": "disabled" if not self.input_interpreter_enabled else "skipped",
            "used": False,
            "called": False,
            "candidate_count": 0,
            "fallback": "deterministic",
        }
        interpreted: dict[str, Any] | None = None
        ai_activity_applied = False
        ai_address_applied = False
        ai_parameter_fields: list[str] = []
        deterministic_address = extract_address(question)
        deterministic_query_activity: dict[str, Any] | None = None
        possible_compound_activity = False
        if question and not explicit_activity and not activity_code:
            # Intentar primero el catálogo determinístico; pero no asumir que la
            # coincidencia más larga es la única actividad mencionada cuando el
            # usuario enumera posibles rubros antes de indicar la ubicación.
            deterministic_query_activity = await self.activities.resolve_from_text(question)
            activity_prefix = re.split(
                r"\b(?:en|sobre|ubicad[oa]s?|direcci[oó]n)\b",
                question,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]
            possible_compound_activity = bool(re.search(
                r"\b(?:y|o|adem[aá]s|tambi[eé]n|junto con|as[ií] como)\b",
                activity_prefix,
                flags=re.IGNORECASE,
            ))
        needs_ai_activity = bool(
            deterministic_query_activity
            and (
                deterministic_query_activity.get("status") == "not_found"
                or possible_compound_activity
            )
        )
        has_parameter_cues = bool(re.search(
            r"\b(superficie|área|area|m2|m²|metros? cuadrados?|ancho de (?:la )?calle|ancho vial|frente|fachada)\b",
            question,
            flags=re.IGNORECASE,
        ))
        needs_ai_candidates = bool(question) and (
            needs_ai_activity
            or (not address_input and not deterministic_address)
            or (
                has_parameter_cues
                and any(value is None for value in (surface_m2, street_width_m, frontage_m))
            )
        )
        if self.input_interpreter_enabled and needs_ai_candidates:
            input_stage["called"] = True
            input_stage["status"] = "running"
            try:
                if self.input_interpreter is None:
                    raise InputInterpreterError("No se configuró el servicio de interpretación.")
                interpreted = await asyncio.wait_for(
                    self.input_interpreter.interpret(question),
                    timeout=self.input_interpreter_timeout_seconds,
                )
                input_stage["status"] = "completed"
                input_stage["candidate_count"] = (
                    len(interpreted.get("activity_candidates", []))
                    + int(bool(interpreted.get("address_candidate")))
                    + sum(interpreted.get(name) is not None for name in ("surface_m2", "street_width_m", "frontage_m"))
                )
                if interpreted.get("rejected_candidate_count", 0):
                    input_warnings.append("AI_INPUT_INTERPRETER_CANDIDATE_REJECTED")
            except Exception as exc:
                # Fail open to deterministic extraction. Do not log query content.
                logger.warning("Intérprete de entrada no disponible; se usa fallback determinístico (%s).", type(exc).__name__)
                interpreted = None
                input_stage["status"] = "unavailable_fallback"
                input_warnings.append("AI_INPUT_INTERPRETER_UNAVAILABLE")

        if activity_code:
            selected = await self.activities.resolve_by_code(activity_code)
            if selected is not None:
                # A code is an explicit catalog selection. If a human-facing label
                # is also supplied, reject only a deterministic conflict with a
                # different catalog record; do not require users to know the code.
                label_resolution = (
                    await self.activities.resolve_detailed(explicit_activity)
                    if explicit_activity else None
                )
                label_activity = label_resolution.get("activity") if label_resolution else None
                if (
                    label_activity is not None
                    and int(label_activity.get("id", -1)) != int(selected.get("id", -2))
                ):
                    activity_resolution = {
                        "status": "ambiguous",
                        "activity": None,
                        "candidates": [selected, label_activity],
                    }
                    resolution_method = "activity_code_label_conflict"
                    user_confirmed = False
                    input_warnings.append("ACTIVITY_CODE_AND_NAME_CONFLICT")
                else:
                    activity_resolution = {"status": "resolved", "activity": selected, "candidates": []}
                    resolution_method = "catalog_code"
                    user_confirmed = True
                    if explicit_activity and label_activity is None:
                        # The code stays authoritative, but retain that the typed
                        # colloquial label did not itself match the current catalog.
                        input_warnings.append("ACTIVITY_LABEL_NOT_MATCHED_TO_CATALOG_CODE")
            elif explicit_activity:
                # A bad optional code must not block a valid name/alias. The warning
                # makes the fallback visible in the response.
                activity_resolution = await self.activities.resolve_detailed(explicit_activity)
                resolution_method = "explicit_activity_after_invalid_code"
                user_confirmed = activity_resolution["status"] == "resolved"
                input_warnings.append("ACTIVITY_CODE_NOT_FOUND_NAME_USED")
            else:
                activity_resolution = {"status": "not_found", "activity": None, "candidates": []}
                resolution_method = "catalog_code_not_found"
                user_confirmed = False
        elif explicit_activity:
            activity_resolution = await self.activities.resolve_detailed(explicit_activity)
            resolution_method = "explicit_activity"
            user_confirmed = activity_resolution["status"] == "resolved"
            if activity_resolution["status"] == "not_found":
                # Return suggestions from the deterministic catalog search without
                # silently selecting a lexical/partial match as the legal activity.
                suggestions = await self.activities.search_catalog(explicit_activity, limit=5)
                if suggestions.get("items"):
                    activity_resolution = {
                        "status": "ambiguous",
                        "activity": None,
                        "candidates": suggestions["items"],
                    }
        else:
            activity_resolution = deterministic_query_activity or await self.activities.resolve_from_text(question)
            resolution_method = "catalog_match_in_query"
            user_confirmed = bool(confirm_activity and activity_resolution["status"] == "resolved")

        # Si la actividad no fue reconocida de forma determinística, las menciones
        # validadas del intérprete quedan disponibles para explicar la aclaración,
        # incluso si el catálogo no devuelve candidatos compatibles.
        if interpreted and needs_ai_activity and interpreted.get("activity_candidates"):
            ai_activity_applied = True

        # El intérprete no reemplaza una resolución determinística existente. Solo
        # aporta menciones si falta rubro; el catálogo sigue siendo la autoridad.
        if (
            interpreted
            and not activity_code
            and not explicit_activity
            and (
                activity_resolution.get("status") == "not_found"
                or possible_compound_activity
            )
        ):
            catalog_candidates: dict[int, dict[str, Any]] = {}
            exact_matches: dict[int, dict[str, Any]] = {}
            for mention in interpreted.get("activity_candidates", []):
                candidate_text = str(mention.get("text", "")).strip()
                if not candidate_text:
                    continue
                resolution = await self.activities.resolve_detailed(candidate_text)
                if resolution.get("status") == "resolved" and resolution.get("activity"):
                    candidate = resolution["activity"]
                    candidate_id = int(candidate["id"])
                    exact_matches[candidate_id] = candidate
                    catalog_candidates[candidate_id] = candidate
                elif resolution.get("status") == "ambiguous":
                    for candidate in resolution.get("candidates", []):
                        catalog_candidates[int(candidate["id"])] = candidate
                else:
                    # Search results are suggestions only, never silently selected.
                    suggestions = await self.activities.search_catalog(candidate_text, limit=5)
                    for candidate in suggestions.get("items", []):
                        catalog_candidates[int(candidate["id"])] = candidate

            if (
                not possible_compound_activity
                and len(interpreted.get("activity_candidates", [])) == 1
                and len(exact_matches) == 1
                and len(catalog_candidates) == 1
            ):
                selected = next(iter(exact_matches.values()))
                activity_resolution = {"status": "resolved", "activity": selected, "candidates": []}
                resolution_method = "ai_mention_validated_catalog"
                user_confirmed = bool(confirm_activity)
                ai_activity_applied = True
            elif catalog_candidates:
                activity_resolution = {
                    "status": "ambiguous", "activity": None,
                    "candidates": sorted(catalog_candidates.values(), key=lambda item: (str(item.get("code", "")), str(item.get("name", "")))),
                }
                resolution_method = "ai_candidates_catalog_suggestions"
                user_confirmed = False
                ai_activity_applied = True

        ai_address: str | None = None
        if (
            interpreted
            and not address_input
            and not deterministic_address
            and isinstance(interpreted.get("address_candidate"), dict)
        ):
            ai_address = interpreted["address_candidate"].get("value")
            ai_address_applied = bool(ai_address)

        # Los parámetros estructurados por el modelo solo rellenan campos no
        # informados y conservan evidencia. Nunca pisan valores explícitos.
        effective_parameters = {
            "surface_m2": surface_m2,
            "street_width_m": street_width_m,
            "frontage_m": frontage_m,
        }
        if interpreted:
            upper_bounds = {"surface_m2": 1_000_000, "street_width_m": 1_000, "frontage_m": 1_000}
            for field_name, maximum in upper_bounds.items():
                value = interpreted.get(field_name)
                if effective_parameters[field_name] is None and value is not None:
                    if isinstance(value, (int, float)) and 0 < value <= maximum:
                        effective_parameters[field_name] = float(value)
                        ai_parameter_fields.append(field_name)
                    else:
                        interpreted["rejected_candidate_count"] = int(interpreted.get("rejected_candidate_count", 0)) + 1
                        input_warnings.append("AI_INPUT_INTERPRETER_CANDIDATE_REJECTED")
        surface_m2 = effective_parameters["surface_m2"]
        street_width_m = effective_parameters["street_width_m"]
        frontage_m = effective_parameters["frontage_m"]

        input_stage["used"] = bool(ai_activity_applied or ai_address_applied or ai_parameter_fields)
        if input_stage["status"] == "completed" and input_stage["candidate_count"] == 0:
            input_stage["status"] = "completed_no_candidates"
        if input_stage["used"]:
            input_stage["fallback"] = None

        # La dirección explícita tiene precedencia; el patrón determinístico es
        # segundo y una dirección extraída por IA es el último recurso.
        request_context = build_request_context(
            query=question,
            explicit_activity=explicit_activity or None,
            explicit_address=address_input,
            activity_resolution=activity_resolution,
            ai_extracted_address=ai_address,
        )
        address = request_context["address"]
        activity = activity_resolution.get("activity")
        now = datetime.now(timezone.utc).isoformat()
        base = {
            "contract_version": "1.2",
            "request_id": str(request_id),
            "generated_at": now,
            "query": {
                "text_input": question or None,
                "activity_input": explicit_activity or None,
                "activity_code_input": activity_code,
                "address_input": (address_input or None),
                "address_extracted": request_context["query"].get("address_extracted"),
                "address_extraction_method": request_context["query"].get("address_extraction_method"),
                "address_candidate_evidence": (interpreted or {}).get("address_candidate", {}).get("evidence") if ai_address_applied else None,
                "input_interpretation": {
                    "status": input_stage["status"],
                    "activity_mentions": (interpreted or {}).get("activity_candidates", []) if needs_ai_activity else [],
                    "address_candidate": (interpreted or {}).get("address_candidate") if ai_address_applied else None,
                    "parameter_fields_applied": list(ai_parameter_fields),
                    "rejected_candidate_count": int((interpreted or {}).get("rejected_candidate_count", 0)),
                },
                "address_used": address,
                "parameters": {
                    "surface_m2": surface_m2,
                    "street_width_m": street_width_m,
                    "frontage_m": frontage_m,
                    "include_geometry": include_geometry,
                    "extracted_by_ai": ai_parameter_fields,
                },
            },
            "execution": {
                "mode": "deterministic",
                "ai_used": bool(input_stage["used"]),
                "ai_stages": {
                    "input_interpreter": input_stage,
                    "explanation_generator": {
                        "enabled": False, "status": "disabled", "used": False, "called": False,
                    },
                },
            },
            "activity": None,
            "location": None,
            "territory": {
                "parcel": None,
                "administrative": {"barrio": None, "comuna": None},
                "urbanism": {"status": "unavailable", "mixturas": [], "special_districts": [], "indicators": {}},
                "land_use": [],
                "useful_data": {},
            },
            "compatibility": None,
            "procedure_type_mapping": None,
            "procedures": {"status": "not_loaded", "items": []},
            "sources": [],
            "warnings": list(input_warnings),
        }

        async def finish_early(source_ids: set[int] | None = None) -> dict[str, Any]:
            if source_ids:
                base["sources"] = await self.sources.get_versions(source_ids)
            base["warnings"] = list(dict.fromkeys(base["warnings"]))
            base["metadata"] = {
                "deterministic": True,
                "ai_used": bool(input_stage["used"]),
                "source_count": len(base["sources"]),
                "parcel_geometry_included": False,
            }
            await self._persist_result(
                base, request_id=request_id, activity=base.get("activity"), location=None,
                surface_m2=surface_m2, street_width_m=street_width_m, frontage_m=frontage_m,
            )
            return base

        ambiguous_activity = activity_resolution["status"] == "ambiguous"
        mapping: dict[str, Any] = {}
        procedures: list[dict[str, Any]] = []
        procedure_details_complete = False
        procedure_details_present = False

        if ambiguous_activity:
            base["activity"] = {
                "status": "ambiguous",
                "input": explicit_activity or question,
                "candidates": activity_resolution.get("candidates", []),
                "user_confirmed": False,
            }
            base["warnings"].append("ACTIVITY_CONFIRMATION_REQUIRED")
        elif activity is None:
            base["activity"] = {
                "status": "not_found",
                "input": explicit_activity or question,
                "candidates": activity_resolution.get("candidates", []),
            }
            base["warnings"].append("ACTIVITY_NOT_FOUND_IN_CATALOG")
        else:
            # Un alias provisional reconoce el lenguaje cotidiano, pero no debe
            # transformarse en selección jurídica definitiva sin confirmación.
            if activity.get("match_kind") == "provisional" and not activity_code:
                user_confirmed = False
            base["activity"] = {
                **activity,
                "resolution_method": resolution_method,
                "user_confirmed": user_confirmed,
                "confirmation_required": not user_confirmed,
                "confirmation_status": "confirmed_by_explicit_selection" if user_confirmed else "pending_user_confirmation",
            }
            if not user_confirmed:
                base["warnings"].append("ACTIVITY_CONFIRMATION_REQUIRED")
            if activity.get("mapping_status") == "provisional" or activity.get("match_kind") == "provisional":
                base["warnings"].append("ACTIVITY_CATALOG_MAPPING_PROVISIONAL")

            mapping, procedures = await self._load_procedures(int(activity["id"]))
            base["procedure_type_mapping"] = mapping
            procedure_details_complete = procedure_details_are_complete(procedures)
            procedure_details_present = procedure_details_are_present(procedures)
            procedure_schema_warnings = [
                warning for item in procedures for warning in item.get("detail_warnings", [])
            ]
            base["procedures"] = {
                "status": "available" if procedure_details_complete else ("partial" if procedures else "not_loaded"),
                "classification_is_not_a_procedure_record": True,
                "detail_status": "available" if procedure_details_complete else ("partial" if procedures else "not_loaded"),
                "items": procedures,
            }
            base["warnings"].extend(mapping.get("warnings", []))
            base["warnings"].extend(procedure_schema_warnings)
            if not procedures:
                base["warnings"].append("PROCEDURE_DETAILS_NOT_LOADED")
            elif not procedure_details_complete:
                base["warnings"].append("PROCEDURE_CONTENT_INCOMPLETE")

        # Actividad y dirección se resuelven independientemente. Un rubro sin
        # coincidencia no bloquea la geocodificación ni la consulta territorial.
        if not address:
            if ambiguous_activity:
                base["status"] = "needs_activity_confirmation"
                base["next_action"] = "Seleccionar la actividad del catálogo y enviar una dirección con calle y altura."
            elif activity is None:
                base["status"] = "needs_activity"
                base["next_action"] = "No se reconoció el rubro. Enviar una dirección para recuperar contexto territorial y seleccionar un candidato del catálogo."
            elif not user_confirmed:
                base["status"] = "needs_activity_confirmation"
                base["next_action"] = "Confirmar la actividad mediante su código oficial y enviar una dirección con calle y altura."
            else:
                base["status"] = "needs_address"
                base["next_action"] = "Enviar una dirección de CABA con calle y altura, o corregir la dirección extraída."
                base["warnings"].append("ADDRESS_REQUIRED")
            source_ids = self._collect_source_ids(activity or {}, None, None, None, [], mapping, procedures, None)
            if ambiguous_activity:
                source_ids.update(
                    int(item["source_version_id"])
                    for item in activity_resolution.get("candidates", [])
                    if item.get("source_version_id") is not None
                )
            if source_ids:
                base["sources"] = await self.sources.get_versions(source_ids)
            return await finish_early()

        location = await self.geocoding.geocode(address)
        territory = await self.territory.resolve(location, include_geometry=include_geometry)
        # La geometría se obtiene solo desde ParcelGeometryProvider, que exige una
        # fuente poligonal real con versión `parcelas`; no se acepta un polígono ad hoc
        # en el payload de geocodificación para no falsear su procedencia.
        base["location"] = {
            "address_input": location.input_address,
            "address_normalized": location.normalized_address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "crs": "EPSG:4326" if location.latitude is not None and location.longitude is not None else None,
            "smp": territory.get("smp") or location.smp,
            "street_code": location.street_code,
            "height": location.height,
            "from_cache": location.from_cache,
            "usig_map_url": self.geocoding.map_url(location),
            "source_version_id": location.source_version_id,
            "warnings": location.warnings,
        }
        base["warnings"].extend(location.warnings)
        base["warnings"].extend(territory.get("warnings", []))

        parcel = territory.get("parcel")
        urban_rule = (territory.get("urban_rules") or [None])[0]
        land_use = territory.get("land_use") or []
        if parcel:
            base["territory"]["parcel"] = {
                "id": parcel.get("id"),
                "smp": parcel.get("smp"),
                "partida_ma": parcel.get("partida_ma"),
                "geometry": parcel.get("geometry") if include_geometry else None,
                "source_version_id": parcel.get("source_version_id"),
                "geometry_source_version_id": parcel.get("geometry_source_version_id"),
                "geometry_status": parcel.get("geometry_status", "cached" if parcel.get("geometry_source_version_id") else ("included" if parcel.get("geometry") else "not_included")),
                "geometry_cached": bool(parcel.get("geometry_source_version_id")),
                "match_method": parcel.get("match_method"),
                "match_distance_m": parcel.get("match_distance_m"),
                "confirmation_required": parcel.get("match_method") == "postgis_nearest_within_threshold",
            }
            base["territory"]["administrative"] = {
                "barrio": {"id": parcel.get("barrio_id"), "name": parcel.get("barrio")} if parcel.get("barrio") else None,
                "comuna": {"id": parcel.get("comuna_id"), "name": parcel.get("comuna")} if parcel.get("comuna") else None,
            }
        base["territory"]["urbanism"] = {
            "status": "available" if urban_rule else "unavailable",
            "mixturas": (urban_rule or {}).get("mixturas") or [],
            "special_districts": (urban_rule or {}).get("special_districts") or [],
            "indicators": {
                key: (urban_rule or {}).get(key)
                for key in ("sm", "catalogado", "rh", "ensanche", "apertura", "lep", "ci_digital", "anac")
                if (urban_rule or {}).get(key) is not None
            },
            "source_version_id": (urban_rule or {}).get("source_version_id"),
            "rule_id": (urban_rule or {}).get("id"),
        }
        if parcel and (not parcel.get("barrio") or not parcel.get("comuna")):
            base["warnings"].append("ADMINISTRATIVE_DATA_INCOMPLETE")
        if include_geometry and parcel and not parcel.get("geometry"):
            base["warnings"].append("PARCEL_GEOMETRY_UNAVAILABLE")
        base["territory"]["land_use"] = land_use
        base["territory"]["useful_data"] = location.useful_data or {}
        base["territory"]["adjacent_streets"] = location.adjacent_streets or []
        base["territory"]["resolution_status"] = territory.get("resolution_status")
        base["territory"]["candidate_parcels"] = territory.get("candidate_parcels", [])

        if ambiguous_activity:
            base["status"] = "needs_activity_confirmation"
            base["next_action"] = "La ubicación y el contexto territorial ya están recuperados; elegir un rubro candidato para evaluar compatibilidad y trámites."
            base["warnings"].append("ACTIVITY_CONFIRMATION_REQUIRED")
        elif activity is None:
            base["status"] = "needs_activity"
            base["next_action"] = "La ubicación y el contexto territorial ya están recuperados; seleccionar una actividad del catálogo o revisar los candidatos sugeridos."
            base["warnings"].append("ACTIVITY_NOT_FOUND_IN_CATALOG")
        else:
            # Con una coincidencia única provisional podemos calcular una vista previa
            # determinista, pero el estado final exige confirmar el rubro antes de
            # presentar la evaluación como definitiva.
            compatibility = await self.urban_evaluation.evaluate(
                activity, urban_rule,
                surface_m2=surface_m2,
                street_width_m=street_width_m,
                frontage_m=frontage_m,
            )
            compatibility["activity_confirmation_required"] = not user_confirmed
            compatibility["activity_mapping_provisional"] = bool(
                activity.get("mapping_status") == "provisional" or activity.get("match_kind") == "provisional"
            )
            base["compatibility"] = compatibility
            if compatibility.get("status") == "insufficient_data":
                base["warnings"].append("URBAN_COMPATIBILITY_INSUFFICIENT_DATA")

            if not user_confirmed:
                base["status"] = "needs_activity_confirmation"
                base["next_action"] = "La ubicación y el contexto territorial ya están recuperados; confirmar el rubro sugerido para convertir esta vista previa en una evaluación determinista definitiva."
                base["warnings"].append("ACTIVITY_CONFIRMATION_REQUIRED")
            elif territory.get("resolution_status") == "ambiguous":
                base["status"] = "partial"
                base["warnings"].append("PARCEL_MATCH_AMBIGUOUS")
            elif territory.get("resolution_status") != "resolved":
                base["status"] = "partial"
            else:
                # La clasificación del Anexo II identifica el tipo de trámite, pero
                # no implica que requisitos/pasos detallados estén cargados.
                all_source_ids = self._collect_source_ids(activity or {}, location, parcel, urban_rule, land_use, mapping, procedures, compatibility)
                base["sources"] = await self.sources.get_versions(all_source_ids)
                required_ok = (
                    urban_rule is not None
                    and compatibility.get("status") != "insufficient_data"
                    and mapping.get("status") == "confirmed"
                    and procedure_details_present
                    and activity.get("mapping_status") == "official"
                    and not location.warnings
                    and not any(warning in base["warnings"] for warning in (
                        "SPECIAL_DISTRICTS_TABLE_UNAVAILABLE", "LAND_USE_TABLE_UNAVAILABLE",
                        "ADMINISTRATIVE_DATA_INCOMPLETE",
                    ))
                    and not (include_geometry and not (parcel or {}).get("geometry"))
                    # Un candidato próximo exige confirmación explícita.
                    and (parcel or {}).get("match_method") != "postgis_nearest_within_threshold"
                )
                base["status"] = "resolved" if required_ok else "partial"
        if not base["sources"]:
            all_source_ids = self._collect_source_ids(activity or {}, location, parcel, urban_rule, land_use, mapping, procedures, base.get("compatibility"))
            if ambiguous_activity:
                all_source_ids.update(
                    int(item["source_version_id"])
                    for item in activity_resolution.get("candidates", [])
                    if item.get("source_version_id") is not None
                )
            base["sources"] = await self.sources.get_versions(all_source_ids)
        # Mantener advertencias estables sin duplicados y orden de aparición.
        base["warnings"] = list(dict.fromkeys(base["warnings"]))
        base["metadata"] = {
            "deterministic": True,
            "ai_used": bool(input_stage["used"]),
            "source_count": len(base["sources"]),
            "parcel_geometry_included": bool(include_geometry and parcel and parcel.get("geometry")),
        }
        await self._persist_result(
            base, request_id=request_id, activity=activity, location=location,
            surface_m2=surface_m2, street_width_m=street_width_m, frontage_m=frontage_m,
        )
        return base

    async def _persist_result(
        self, result: dict[str, Any], *, request_id: uuid.UUID, activity: dict[str, Any] | None,
        location: Any, surface_m2: float | None, street_width_m: float | None, frontage_m: float | None,
    ) -> None:
        # Sin repositorio (pruebas unitarias puras) el servicio conserva su contrato
        # funcional sin simular una escritura. En producción main.py siempre lo inyecta.
        if self.queries is None:
            result["trace"] = {"query_run_id": None, "persistence_status": "not_configured"}
            return

        query_id = uuid.uuid4()
        result["trace"] = {"query_run_id": str(query_id), "persistence_status": "pending"}
        query_input = result.get("query") or {}
        loc = result.get("location") or {}
        territory = result.get("territory") or {}
        parcel = territory.get("parcel") or {}
        urbanism = territory.get("urbanism") or {}
        compatibility = result.get("compatibility") or {}
        source_ids = {
            int(item["source_version_id"]) for item in result.get("sources", [])
            if item.get("source_version_id") is not None
        }
        activity_rule_ids = [
            int(item["activity_use_rule_id"])
            for item in compatibility.get("evaluations", [])
            if item.get("activity_use_rule_id") is not None
        ]
        procedure_rule_ids = [
            int(item["id"]) for procedure in (result.get("procedures") or {}).get("items", [])
            for item in procedure.get("reglas", []) if item.get("id") is not None
        ]
        question = query_input.get("text_input") or (
            f"{(activity or {}).get('name') or query_input.get('activity_input') or 'Actividad'} — "
            f"{query_input.get('address_used') or query_input.get('address_input') or 'sin dirección'}"
        )
        activity_input = (
            query_input.get("activity_input") or query_input.get("activity_code_input")
            or (activity or {}).get("name") or (activity or {}).get("input")
        )
        raw_input = {
            **query_input,
            "surface_m2": surface_m2,
            "street_width_m": street_width_m,
            "frontage_m": frontage_m,
        }
        try:
            audit_result = await self.queries.record_territory_result(
                query_id=query_id, request_id=request_id, question=question, activity_input=activity_input,
                activity_id=int(activity["id"]) if activity and activity.get("id") is not None else None,
                address_input=query_input.get("address_input") or query_input.get("address_used"),
                normalized_address=loc.get("address_normalized"), street_code=loc.get("street_code"),
                latitude=loc.get("latitude"), longitude=loc.get("longitude"),
                surface_m2=surface_m2, street_width_m=street_width_m, frontage_m=frontage_m,
                parcel_id=int(parcel["id"]) if parcel.get("id") is not None else None,
                input_payload=raw_input, response_payload=result, source_version_ids=source_ids,
                activity_use_rule_ids=activity_rule_ids,
                urban_parcel_rule_id=int(urbanism["rule_id"]) if urbanism.get("rule_id") is not None else None,
                procedure_rule_ids=procedure_rule_ids,
            )
            audit_result = audit_result if isinstance(audit_result, dict) else {"status": "stored", "warnings": []}
            persistence_status = audit_result.get("status", "stored")
            result["trace"] = {
                "query_run_id": str(query_id) if persistence_status != "unavailable" else None,
                "persistence_status": persistence_status,
                "audit_schema": audit_result.get("audit_schema"),
                "evidence_rows": audit_result.get("evidence_rows"),
            }
            result["warnings"].extend(audit_result.get("warnings", []))
        except Exception:
            # La auditoría no debe invalidar una resolución determinista ya calculada.
            # Se deja una advertencia visible para que staging/observabilidad la detecten.
            logger.exception("No se pudo persistir auditoría territorial request_id=%s", request_id)
            result["trace"] = {"query_run_id": None, "persistence_status": "unavailable"}
            result["warnings"].append("QUERY_AUDIT_PERSISTENCE_UNAVAILABLE")
        result["warnings"] = list(dict.fromkeys(result.get("warnings", [])))

    async def _load_procedures(self, activity_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        mapping, procedures = await asyncio.gather(
            self.mappings.for_activity(activity_id), self.procedures.resolve(activity_id)
        )
        return mapping, procedures

    async def _source_versions(
        self, activity: dict[str, Any], mapping: dict[str, Any], location: Any,
        procedures: list[dict[str, Any]], other: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        ids = set()
        for value in (activity.get("source_version_id"), activity.get("alias_source_version_id"), mapping.get("source_version_id")):
            if value is not None:
                ids.add(int(value))
        if location and location.source_version_id is not None:
            ids.add(int(location.source_version_id))
        ids.update(self._procedure_source_ids(procedures))
        ids.update(self._dict_source_ids(other))
        return await self.sources.get_versions(ids)

    def _collect_source_ids(
        self, activity: dict[str, Any], location: Any, parcel: dict[str, Any] | None,
        urban_rule: dict[str, Any] | None, land_use: list[dict[str, Any]],
        mapping: dict[str, Any], procedures: list[dict[str, Any]], compatibility: dict[str, Any] | None,
    ) -> set[int]:
        ids: set[int] = set()
        for value in (activity.get("source_version_id"), activity.get("alias_source_version_id"), mapping.get("source_version_id")):
            if value is not None:
                ids.add(int(value))
        if location and location.source_version_id is not None:
            ids.add(int(location.source_version_id))
        if parcel:
            for key in ("source_version_id", "geometry_source_version_id"):
                if parcel.get(key) is not None:
                    ids.add(int(parcel[key]))
        if urban_rule and urban_rule.get("source_version_id") is not None:
            ids.add(int(urban_rule["source_version_id"]))
        if urban_rule:
            ids.update(self._dict_source_ids(urban_rule.get("special_districts") or []))
        ids.update(self._dict_source_ids(land_use))
        ids.update(self._procedure_source_ids(procedures))
        if compatibility:
            ids.update(self._dict_source_ids(compatibility.get("evaluations", [])))
        return ids

    @staticmethod
    def _dict_source_ids(items: list[dict[str, Any]]) -> set[int]:
        ids: set[int] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get("source_version_id")
            if value is not None:
                ids.add(int(value))
        return ids

    def _procedure_source_ids(self, procedures: list[dict[str, Any]]) -> set[int]:
        ids: set[int] = set()
        for procedure in procedures:
            for value in (procedure.get("source_version_id"), procedure.get("procedure_source_version_id")):
                if value is not None:
                    ids.add(int(value))
            for collection_name in ("requisitos", "documentos", "pasos", "reglas", "variantes"):
                ids.update(self._dict_source_ids(procedure.get(collection_name) or []))
        return ids
