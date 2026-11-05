"""Normalización central de códigos Anexo II -> procedure_variants.code.

Los códigos de entrada son códigos de clasificación; los códigos canónicos son
los almacenados en procedure_variants. No se inventan variantes inexistentes.
"""
from __future__ import annotations

ANEXO_II_TO_VARIANT = {
    "DDRR_CP": "DDRR_CON_PLANO",
    "DDRR_SP": "DDRR_SIN_PLANO",
    "LICENCIA": "LICENCIA",
}

def canonical_variant_code(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.strip().upper()
    return ANEXO_II_TO_VARIANT.get(normalized, normalized)

# SQL expression for candidate.code inside ProcedureRepository. Keep in sync with
# ANEXO_II_TO_VARIANT and cover only known aliases; unknown codes pass through and
# therefore fail to join unless an explicit variant exists.
VARIANT_CODE_SQL_CASE = "CASE candidate.code " + " ".join(
    f"WHEN '{source}' THEN '{target}'" for source, target in ANEXO_II_TO_VARIANT.items()
) + " ELSE candidate.code END"
