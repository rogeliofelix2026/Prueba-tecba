"""
Divide texto documental en chunks respetando encabezados y páginas para alimentar el RAG.

`structure_aware_chunks()` recibe una lista de páginas y devuelve objetos `Chunk` con
contenido, ruta de encabezados y rango de páginas. `max_chars` y `overlap_chars` controlan
tamaño y solapamiento entre chunks.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    content: str
    heading_path: str
    page_from: int | None = None
    page_to: int | None = None


_HEADING_RE = re.compile(r"^(TÍTULO|CAPÍTULO|SECCIÓN|ANEXO|ARTÍCULO)\b", re.IGNORECASE)
_HEADING_LEVELS = {"ANEXO": 0, "TÍTULO": 0, "CAPÍTULO": 1, "SECCIÓN": 2, "ARTÍCULO": 3}


def _heading_level(line: str) -> int | None:
    match = _HEADING_RE.match(line)
    return _HEADING_LEVELS.get(match.group(1).upper()) if match else None


def structure_aware_chunks(
    pages: list[str],
    max_chars: int = 3000,
    overlap_chars: int = 300,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_len = 0
    first_page: int | None = None
    last_page: int | None = None
    headings: list[tuple[int, str]] = []
    buffer_has_body = False

    def heading_path() -> str:
        return " > ".join(item[1] for item in headings)

    def flush() -> None:
        nonlocal buffer, buffer_len, first_page, last_page, buffer_has_body
        if not buffer:
            return
        content = "\n".join(buffer).strip()
        if content:
            chunks.append(Chunk(content, heading_path(), first_page, last_page))
        tail = content[-overlap_chars:].strip() if overlap_chars > 0 else ""
        buffer = [tail] if tail else []
        buffer_len = len(tail)
        first_page = last_page
        buffer_has_body = bool(tail)

    for page_number, page_text in enumerate(pages, start=1):
        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue
            level = _heading_level(line)
            if level is not None:
                if buffer and buffer_has_body:
                    flush()
                headings[:] = [(lvl, text) for lvl, text in headings if lvl < level]
                headings.append((level, line))

            required = len(line) + (1 if buffer else 0)
            if buffer and buffer_len + required > max_chars:
                flush()
            if first_page is None:
                first_page = page_number
            last_page = page_number
            buffer.append(line)
            buffer_len += len(line) + (1 if buffer_len else 0)
            if level is None:
                buffer_has_body = True

    flush()
    return chunks
