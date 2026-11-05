"""Reglas determinísticas del Cuadro de Usos N.º 3.3.

Este módulo separa dos responsabilidades:
- interpretar el valor publicado por el Cuadro 3.3 en un modelo consultable;
- evaluar preliminarmente una actividad contra una o más Áreas de Mixtura.

La evaluación es orientativa y conserva el valor original para trazabilidad.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

STATUS_RANK = {
    "not_compatible": 0,
    "council_review": 1,
    "conditional": 2,
    "compatible": 3,
}


@dataclass(frozen=True, slots=True)
class ParsedUseRule:
    raw_value: str
    status: str
    max_surface_m2: Decimal | None = None
    exceeds_max_requires_council: bool = False
    requires_street_width_min_m: Decimal | None = None
    requires_frontage_min_m: Decimal | None = None
    requires_frontage_max_m: Decimal | None = None
    min_surface_m2: Decimal | None = None
    special_condition: str | None = None


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def parse_use_rule(raw_value: str) -> ParsedUseRule:
    raw = (raw_value or "").strip().upper()

    if raw == "SI":
        return ParsedUseRule(raw, "compatible")
    if raw in {"NO", "NPC"}:
        return ParsedUseRule(raw, "not_compatible")
    if raw == "C":
        return ParsedUseRule(raw, "council_review", special_condition="Requiere evaluación del Consejo.")
    if raw == "SCPC":
        return ParsedUseRule(
            raw,
            "conditional",
            special_condition="Solo depósitos de las clases permitidas según el Cuadro 3.13.1.5.",
        )
    if raw == "AMP12":
        return ParsedUseRule(
            raw,
            "conditional",
            requires_frontage_min_m=Decimal("12"),
            special_condition="La parcela necesita al menos 12 m de frente.",
        )

    parts = [part for part in re.split(r"[ /]+", raw) if part]
    numeric = None
    requires_council = False
    requires_street = False
    special = []

    for part in parts:
        if part == "SA":
            requires_street = True
            continue
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(C|B|SA)?", part)
        if not match:
            special.append(part)
            continue
        numeric = _decimal(match.group(1))
        suffix = match.group(2)
        if suffix == "C":
            requires_council = True
        elif suffix == "SA":
            requires_street = True
        elif suffix == "B":
            # El dataset de referencia usa "b" en reglas cuyo texto explica
            # el límite de frente/superficie. Conservamos la interpretación
            # conocida de la aplicación de referencia como condición revisable.
            if numeric == Decimal("1200"):
                special.append("Superficie mínima 200 m².")
            else:
                special.append("Verificar condición de frente máxima según la normativa aplicable.")

    if numeric is None and requires_street:
        return ParsedUseRule(
            raw,
            "conditional",
            requires_street_width_min_m=Decimal("26"),
            special_condition="Solo sobre calles de 26 m de ancho o más.",
        )

    if numeric is not None:
        return ParsedUseRule(
            raw,
            "conditional",
            max_surface_m2=numeric,
            exceeds_max_requires_council=requires_council,
            requires_street_width_min_m=Decimal("26") if requires_street else None,
            special_condition=" ".join(special) or None,
        )

    return ParsedUseRule(raw, "conditional", special_condition="Revisar condición normativa específica.")


def evaluate_use_rule(
    rule: dict[str, Any],
    surface_m2: float | None = None,
    street_width_m: float | None = None,
    frontage_m: float | None = None,
) -> dict[str, Any]:
    """Evalúa una regla ya parseada.

    No infiere el ancho de calle a partir de que una vía sea avenida: si la regla
    exige 26 m y no tenemos ese dato, el resultado queda como condicional.
    """
    status = str(rule["status"])
    notes: list[str] = []

    if rule.get("special_condition"):
        notes.append(str(rule["special_condition"]))

    max_surface = rule.get("max_surface_m2")
    if max_surface is not None and surface_m2 is not None:
        max_value = float(max_surface)
        if surface_m2 > max_value:
            if rule.get("exceeds_max_requires_council"):
                status = "council_review"
                notes.append(
                    f"La superficie ({surface_m2:g} m²) supera el máximo de {max_value:g} m²; requiere evaluación del Consejo."
                )
            else:
                status = "not_compatible"
                notes.append(
                    f"La superficie ({surface_m2:g} m²) supera el máximo de {max_value:g} m²."
                )
        else:
            notes.append(
                f"La superficie ({surface_m2:g} m²) está dentro del máximo de {max_value:g} m²."
            )
    elif max_surface is not None:
        notes.append(f"Superficie máxima: {float(max_surface):g} m².")

    min_surface = rule.get("min_surface_m2")
    if min_surface is not None:
        if surface_m2 is None:
            status = max(status, "conditional", key=STATUS_RANK.get)
            notes.append(f"Debe verificarse una superficie mínima de {float(min_surface):g} m².")
        elif surface_m2 < float(min_surface):
            status = "not_compatible"
            notes.append(f"La superficie debe ser de al menos {float(min_surface):g} m².")

    min_width = rule.get("requires_street_width_min_m")
    if min_width is not None:
        if street_width_m is None:
            status = max(status, "conditional", key=STATUS_RANK.get)
            notes.append(f"Falta verificar ancho de calle ≥ {float(min_width):g} m.")
        elif street_width_m < float(min_width):
            status = "not_compatible"
            notes.append(
                f"El ancho de calle ({street_width_m:g} m) es menor a {float(min_width):g} m."
            )
        else:
            notes.append(f"El ancho de calle ({street_width_m:g} m) cumple ≥ {float(min_width):g} m.")

    min_frontage = rule.get("requires_frontage_min_m")
    if min_frontage is not None:
        if frontage_m is None:
            status = max(status, "conditional", key=STATUS_RANK.get)
            notes.append(f"Falta verificar frente de parcela ≥ {float(min_frontage):g} m.")
        elif frontage_m < float(min_frontage):
            status = "not_compatible"
            notes.append(f"El frente de parcela debe ser de al menos {float(min_frontage):g} m.")

    max_frontage = rule.get("requires_frontage_max_m")
    if max_frontage is not None:
        if frontage_m is None:
            status = max(status, "conditional", key=STATUS_RANK.get)
            notes.append(f"Falta verificar frente de parcela ≤ {float(max_frontage):g} m.")
        elif frontage_m > float(max_frontage):
            status = "not_compatible"
            notes.append(f"El frente de parcela excede {float(max_frontage):g} m.")

    return {
        "status": status,
        "status_rank": STATUS_RANK[status],
        "notes": notes,
    }


def evaluate_activity(
    activity: dict[str, Any],
    urban_rule: dict[str, Any] | None,
    *,
    surface_m2: float | None = None,
    street_width_m: float | None = None,
    frontage_m: float | None = None,
) -> dict[str, Any]:
    """Evalúa la actividad en cada mixtura disponible sin elegir datos inexistentes.

    Acepta el esquema compacto ``mixturas SMALLINT[]`` y el esquema legado
    ``uso_1/uso_2/uso_3``. Si la parcela tiene más de una mixtura, se mantiene
    el detalle de todas y se elige la situación más favorable, como hace la
    herramienta de referencia, preservando los casos condicionados/distritos.
    """
    if not urban_rule:
        return {
            "status": "insufficient_data",
            "activity": activity,
            "mixturas": [],
            "reason": "No hay regla urbanística asociada a la parcela/SMP.",
            "evaluations": [],
        }

    supplied = urban_rule.get("mixturas")
    if isinstance(supplied, (list, tuple)):
        values = list(supplied)
    else:
        values = [urban_rule.get(key) for key in ("uso_1", "uso_2", "uso_3")]

    mixturas: list[int] = []
    for value in values:
        try:
            mixtura = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= mixtura <= 4 and mixtura not in mixturas:
            mixturas.append(mixtura)
    mixturas.sort()

    evaluations: list[dict[str, Any]] = []
    activity_rules = urban_rule.get("activity_rules") or {}
    for mixtura in mixturas:
        raw_rule = activity_rules.get(str(mixtura)) or activity_rules.get(mixtura)
        if not raw_rule:
            continue
        evaluated = evaluate_use_rule(
            raw_rule,
            surface_m2=surface_m2,
            street_width_m=street_width_m,
            frontage_m=frontage_m,
        )
        evaluations.append({
            "mixtura": mixtura,
            "activity_use_rule_id": raw_rule.get("id"),
            "raw_value": raw_rule.get("raw_value"),
            "source_version_id": raw_rule.get("source_version_id"),
            **evaluated,
        })

    if not evaluations:
        return {
            "status": "insufficient_data",
            "activity": activity,
            "mixturas": mixturas,
            "reason": (
                "No hay mixturas para evaluar."
                if not mixturas
                else "La parcela tiene mixturas, pero no existe una regla cargada para la actividad en esas mixturas."
            ),
            "evaluations": [],
            "special_districts": urban_rule.get("special_districts") or [],
            "basis": {
                "urban_parcel_rule_id": urban_rule.get("id"),
                "source_version_id": urban_rule.get("source_version_id"),
            },
        }

    # Orden estable: el primer orden de criterio es el estado más favorable y,
    # ante empate, la mixtura más baja para que la respuesta sea reproducible.
    best = max(evaluations, key=lambda item: (item["status_rank"], -item["mixtura"]))
    notes = list(best["notes"])
    status = best["status"]
    special_districts = urban_rule.get("special_districts") or []
    if special_districts and status not in {"not_compatible", "council_review"}:
        status = "conditional"
        notes.append(
            "La parcela presenta uno o más distritos especiales; debe revisarse la normativa específica antes de concluir compatibilidad."
        )

    return {
        "status": status,
        "activity": activity,
        "mixturas": mixturas,
        "selected_mixtura": best["mixtura"],
        "notes": notes,
        "evaluations": evaluations,
        "special_districts": special_districts,
        "inputs": {
            "surface_m2": surface_m2,
            "street_width_m": street_width_m,
            "frontage_m": frontage_m,
        },
        "basis": {
            "rule": "Cuadro de Usos del Suelo N.º 3.3",
            "source_version_id": urban_rule.get("source_version_id"),
            "urban_parcel_rule_id": urban_rule.get("id"),
        },
    }
