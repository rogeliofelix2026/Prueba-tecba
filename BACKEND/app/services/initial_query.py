"""Extracción determinista de actividad y dirección desde la consulta inicial.

La extracción es intencionalmente conservadora: usa el catálogo de actividades
cargado en BD y patrones de calle/altura; no inventa actividad ni dirección.
"""
from __future__ import annotations

import re
from typing import Any


# Admitimos direcciones de CABA con nomenclaturas habituales. El ancla de
# preposición evita absorber el texto anterior (p. ej. "quiero abrir un local").
_STREET_PREFIX = r"(?:(?:av(?:enida)?|calle|diag(?:onal)?|pje\.?|pasaje|tte\.?|gral\.?|ing\.?|dr\.?|dra\.?)\s+)?"
_STREET_CHARS = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9.'’ -]{1,65}?"
_HEIGHT_BOUNDARY = (
    r"(?=\s*(?:,?\s*(?:CABA|Ciudad Autónoma de Buenos Aires))?"
    r"(?:\s*$|[.!?;,:]|\s+(?:con|para|y|que|qué|donde|dónde|como|cómo|"
    r"necesito|quiero|local|superficie|área|area)\b|"
    r"\s+de\s+\d+(?:[.,]\d+)?\s*(?:m2|m²|metros? cuadrados?)\b))"
)
_ADDRESS_PATTERNS = (
    # La dirección después de una preposición se puede encontrar dentro de una
    # consulta larga, incluso si luego vienen otras preguntas o la superficie.
    re.compile(
        r"\b(?:en|sobre|direcci[oó]n\s*:?|ubicad[oa]s?\s+en)\s+"
        rf"(?P<street>{_STREET_PREFIX}{_STREET_CHARS})\s+(?P<height>\d{{1,5}})\b"
        + _HEIGHT_BOUNDARY,
        re.IGNORECASE,
    ),
    # Fallback deliberadamente anclado: solo admite la dirección si el texto
    # completo es una dirección, nunca si la consulta entera es una frase.
    re.compile(
        rf"^\s*(?P<street>{_STREET_PREFIX}[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9.'’ -]{{2,65}}?)\s+"
        r"(?P<height>\d{1,5})\b"
        r"(?:\s*,?\s*(?:CABA|Ciudad Autónoma de Buenos Aires))?\s*[.!?;:]?\s*$",
        re.IGNORECASE,
    ),
)


def extract_address(text: str) -> str | None:
    """Extrae calle y altura sin confundir superficies con direcciones."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return None
    for pattern in _ADDRESS_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        street = " ".join(match.group("street").split()).strip(" ,.;:")
        # Natural-language Argentine phrasing often says "Corrientes al 2500".
        # The preposition is not part of the street name sent to the geocoder.
        street = re.sub(r"\s+al$", "", street, flags=re.IGNORECASE).strip()
        height = match.group("height")
        tokens = street.casefold().split()
        if len(street) < 2 or not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", street):
            continue
        if len(tokens) > 7:
            continue
        if any(token.strip(".,:") in {"superficie", "área", "area", "m2", "m²", "metros", "local"} for token in tokens):
            continue
        return f"{street} {height}"
    return None


def build_request_context(
    *,
    query: str,
    explicit_activity: str | None,
    explicit_address: str | None,
    activity_resolution: dict[str, Any],
    ai_extracted_address: str | None = None,
) -> dict[str, Any]:
    """Resuelve precedencias y conserva cómo se obtuvo la dirección."""
    activity_status = activity_resolution.get("status", "not_found")
    deterministic_address = extract_address(query)
    if explicit_address and explicit_address.strip():
        address = " ".join(explicit_address.split())
        address_method = "explicit_input"
    elif deterministic_address:
        address = deterministic_address
        address_method = "deterministic_pattern"
    elif ai_extracted_address:
        address = " ".join(ai_extracted_address.split())
        address_method = "ai_interpreter_candidate"
    else:
        address = None
        address_method = "not_found"
    if activity_status == "ambiguous":
        status = "needs_activity_confirmation"
    elif activity_status != "resolved":
        status = "needs_activity"
    elif not address:
        status = "needs_address"
    else:
        status = "ready"
    return {
        "status": status,
        "query": {
            "text_input": query,
            "activity_input": explicit_activity,
            "address_input": explicit_address,
            "address_extracted": address if not explicit_address else None,
            "address_extraction_method": address_method,
        },
        "address": address,
    }
