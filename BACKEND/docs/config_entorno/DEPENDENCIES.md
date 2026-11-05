# Dependencias — SGI Backend

Las dependencias ejecutables están declaradas en `requirements.txt`.

## Runtime

| Dependencia | Uso |
|---|---|
| `fastapi` | API HTTP |
| `uvicorn[standard]` | servidor ASGI |
| `httpx` | USIG y Ollama |
| `psycopg[binary,pool]` | PostgreSQL y pools |
| `pgvector` | adaptación de vectores/halfvec |
| `pydantic` | contratos y validación |
| `pydantic-settings` | configuración por entorno |

## Desarrollo

- `pytest`
- `ruff`
- `pip-audit`

## Ingesta offline

- `PyMuPDF`
- `geopandas`
- `pyogrio`

## Criterio

No agregar una dependencia si el MVP puede resolver la necesidad con una implementación pequeña y mantenible. Evitar librerías cuyo único objetivo sea duplicar funciones simples del estándar o del stack ya instalado.
