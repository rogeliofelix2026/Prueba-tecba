# `POST /api/v1/territory` — matriz de pruebas para Backend, Frontend y QA

Contrato de referencia: `../API_TERRITORY_V0.3.0.md`. Los JSON de esta carpeta son fixtures ficticios; no se usan como resultados esperados de integración contra Supabase.

| ID | Caso | Resultado esperado | Validación clave |
|---|---|---|---|
| T01 | Consulta con `activity_code` explícito y dirección válida | `200`, estado `partial` o `resolved` según los datos efectivos | `execution.ai_used=false`; presencia de `request_id`, `activity`, `location`, `territory`, `compatibility`, mapeo, fuentes y advertencias. |
| T02 | Actividad encontrada en la frase sin confirmación explícita | `200`, `needs_activity_confirmation` | Se devuelve el candidato y `next_action`; no se geocodifica ni evalúa antes de confirmar. |
| T03 | Actividad confirmada pero sin dirección utilizable | `200`, `needs_address` | Incluye tipo de trámite si hay mapeo, estado y fuentes disponibles; no inventa ubicación. |
| T04 | Parcela encontrada pero sin fila en `urban_parcel_rules` | `200`, `partial` | `urbanism.status=unavailable`; compatibilidad `insufficient_data`; nunca afirmar “sin restricciones”. |
| T05 | Regla disponible y no hay distritos especiales, tabla consultable | `200`; `partial` o `resolved` según completitud del resto del flujo | `special_districts=[]` representa ausencia de filas solo si la tabla está disponible. |
| T06 | JSON mal formado, campos con longitud inválida o petición vacía | `422` | Error de validación estable; no se llama a USIG. |
| T07 | Dirección no localizada por USIG | Error explícito según el proveedor | Diferenciar dirección no encontrada de proveedor no disponible. |
| T08 | USIG inaccesible | `502` | Código genérico `geocoding_failed`, con `request_id` en header; no devuelve trazas SQL. |
| T09 | Dirección localizada por USIG, pero sin parcela CABA inequívoca en la BD | `200`, `partial` | Devuelve coordenadas y `PARCEL_NOT_RESOLVED`; no inventa una clasificación “fuera de CABA” si el proveedor no entrega evidencia explícita de jurisdicción. |
| T10 | `include_geometry=true` y geometría disponible | `200` | GeoJSON con coordenadas `[longitud, latitud]`, fuente/versión y parcela inequívoca. |
| T11 | `include_geometry=false` | `200` | `territory.parcel.geometry=null`; `metadata.parcel_geometry_included=false`. |
| T12 | Punto dentro de dos polígonos o en límite ambiguo | `200`, `partial` | `resolution_status=ambiguous`, candidatos si se pueden identificar; no asignar al azar. |
| T13 | Consulta repetida | `200` | Geocache reutilizada según clave; la forma pública se mantiene estable. |
| T14 | Frontend desde origen permitido | Respuesta accesible desde navegador | CORS desde configuración, sin claves Supabase en el cliente. |
| T15 | `/docs` y `/openapi.json` | Disponibles si `DOCS_ENABLED=true` | Campos nullable, estados y respuestas de error coherentes con implementación. |
| T16 | Mapeo Anexo II condicional/no encontrado | `200`, normalmente `partial` | Mantiene alternativas/estado de revisión; no selecciona un tipo por defecto. |
| T17 | Tipo de trámite conocido, detalle de procedimientos vacío | `200`, `partial` | La clasificación se conserva; `procedures.status=not_loaded` y warning `PROCEDURE_DETAILS_NOT_LOADED`. |
| T18 | Esquema incompatible o tablas opcionales ausentes | `503` en readiness/consulta cuando impiden operar, advertencias cuando solo reducen capacidades | No filtra SQL ni intenta reparar automáticamente el esquema. |
| T19 | `parcels` con variantes legacy/compactas soportadas | `200` | Se usan solo columnas detectadas por `information_schema`; sin referencia a columna no existente. |

## Secuencia mínima antes de cerrar v0.3.0

1. Ejecutar `python scripts/migrate.py`, verificar manualmente `supabase migration list --linked` y correr `python scripts/check_db.py` (modo de solo lectura).
2. Probar una dirección real validada por el equipo, una parcela con regla y una sin regla, y comprobar sus fuentes/versiones.
3. Confirmar el flujo de selección de actividad con el Frontend (candidato → `activity_code` → resultado).
4. Probar mapa/contexto y la diferencia entre `mixturas=[]`, tabla ausente y regla ausente.
5. Verificar el camino feliz con mapeo confirmado y procedimiento detallado cargado; documentar el resultado real y no reutilizar IDs de mocks.
6. Repetir las pruebas desde navegador para CORS y revisar `request_id` en logs.
