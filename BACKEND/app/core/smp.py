"""Normalización única y determinista de identificadores catastrales SMP."""
from __future__ import annotations

import re
from typing import Any

_SMP_RE = re.compile(r"^\d{1,3}-[A-Z0-9]+-[A-Z0-9]+$", re.IGNORECASE)


def normalize_smp(value: Any) -> str | None:
    """Normaliza espacios/case y completa la sección a tres dígitos.

    No inventa componentes ni elimina sufijos parcelarios (p. ej. 012F o 053A).
    Retorna None cuando no hay exactamente tres componentes válidos.
    """
    if value is None:
        return None
    text = str(value).strip()
    # Swagger/client tools sometimes serialize quoted query values literally
    # (e.g. %22013-090-006%22). Accept one matching outer quote pair only.
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"\"", "'"}:
        text = text[1:-1].strip()
    text = re.sub(r"\s*[-–—]\s*", "-", text).upper()
    text = re.sub(r"\s+", "", text)
    if not _SMP_RE.fullmatch(text):
        return None
    section, block, parcel = text.split("-")
    result = f"{section.zfill(3)}-{block}-{parcel}"
    return result if _SMP_RE.fullmatch(result) else None
