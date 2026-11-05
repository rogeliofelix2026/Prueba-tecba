# API territorial v0.3.0 — contrato operativo

## Endpoint principal

`POST /api/v1/territory` ejecuta el flujo determinista completo y nunca invoca IA.

Request mínimo recomendado (solo actividad + dirección):

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/territory' \
  -H 'Content-Type: application/json' \
  -d '{"activity":"Cafetería","address":"Corrientes 2500","surface_m2":180,"include_geometry":true}'
```

También se puede enviar solo la consulta en lenguaje natural junto con `activity`; si se puede extraer una dirección de calle + altura, el sistema la usa. Por ejemplo, `query: "Quiero abrir una cafetería en Corrientes al 2500"` normaliza la dirección a `Corrientes 2500`.

También se aceptan `query`, `confirm_activity`, `include_geometry` y `surface_m2`. `street_width_m` y `frontage_m` son opcionales: nunca se requieren como campos de entrada. Cuando una regla los necesite y el sistema no los tenga en sus fuentes, la evaluación debe explicitar la condición o los datos faltantes, no responder HTTP 422.

`activity_code` también es opcional. Si se envían tanto `activity` como `activity_code`, deben apuntar al mismo registro de catálogo; un conflicto devuelve los candidatos en el cuerpo estructurado, sin geocodificar ni decidir arbitrariamente. No se aplica similitud semántica para convertir sinónimos desconocidos en usos legales.

## Forma de respuesta

La respuesta está versionada informalmente como v0.3.0 y usa `snake_case`:

```json
{
  "request_id": "uuid",
  "generated_at": "ISO-8601 UTC",
  "status": "partial",
  "query": {
    "text_input": "...",
    "activity_input": null,
    "activity_code_input": null,
    "address_input": null,
    "address_extracted": "Av. Corrientes 2500",
    "address_used": "Av. Corrientes 2500"
  },
  "execution": {"mode": "deterministic", "ai_used": false},
  "activity": {"id": 1, "code": "...", "name": "...", "user_confirmed": true},
  "location": {
    "address_normalized": "...",
    "latitude": -34.6,
    "longitude": -58.4,
    "crs": "EPSG:4326",
    "smp": "009-061-013",
    "from_cache": true,
    "source_version_id": 1,
    "warnings": []
  },
  "territory": {
    "parcel": {"id": 1, "smp": "009-061-013", "geometry": null},
    "administrative": {"barrio": null, "comuna": null},
    "urbanism": {"status": "available", "mixturas": [2, 3], "special_districts": [], "indicators": {}},
    "land_use": [],
    "useful_data": {},
    "adjacent_streets": [],
    "resolution_status": "resolved",
    "candidate_parcels": []
  },
  "compatibility": {"status": "insufficient_data", "evaluations": []},
  "procedure_type_mapping": {"status": "not_found_in_anexo_ii", "warnings": ["ACTIVITY_MAPPING_NOT_FOUND"]},
  "procedures": {"status": "not_loaded", "items": []},
  "sources": [],
  "warnings": ["PROCEDURE_DETAILS_NOT_LOADED"],
  "metadata": {"deterministic": true, "ai_used": false, "source_count": 0, "parcel_geometry_included": false}
}
```

El JSON es ilustrativo. No copiar IDs, valores de mixtura ni fuente de los mocks al resultado real.

## Estados

| Estado | Significado |
|---|---|
| `needs_activity` | Sin coincidencia explícita en catálogo o alias. |
| `needs_activity_confirmation` | Match implícito o múltiples candidatos; necesita elección. |
| `needs_address` | Actividad confirmada; falta una dirección utilizable. |
| `partial` | La geografía puede resolverse, pero faltan datos, reglas, mapeo confirmado o detalle procedimental. |
| `resolved` | Se cumplen todas las comprobaciones de completitud definidas por el servicio. No es una aprobación legal. |

Compatibilidad (`compatibility.status`) es independiente del estado del flujo:
`compatible`, `conditional`, `council_review`, `not_compatible`, `insufficient_data`.

`mixturas=[]` no significa mixtura libre. `special_districts=[]` solo debe leerse como ausencia de filas cuando la tabla y la consulta están disponibles. No se selecciona la parcela más cercana a un punto: el fallback PostGIS requiere contención inequívoca.

## Endpoints complementarios

| Ruta | Uso |
|---|---|
| `POST /api/v1/geocoding` | Geocodificación/cache/USIG sin evaluación de uso. |
| `GET /api/v1/territory?smp=...` | Recuperación territorial por SMP; acepta también coordenadas como alternativa si el SMP no resuelve. `include_geometry=true` opta por geometría. |
| `POST /api/v1/territory/evaluate` | Evaluar una actividad explícita sobre ubicación/SMP. |
| `GET /api/v1/map/parcel/{smp}` | GeoJSON Feature, o geometría `null` con estado `unavailable`. |
| `GET /api/v1/context/parcel/{smp}` | Parcel ID, administración, reglas, distritos y observaciones de uso. |
| `GET /api/v1/activities/{activity_id}/procedures` | Clasificación Anexo II y detalle procedimental real, si está cargado. |
| `GET /api/v1/ready` | Conectividad + capacidades mínimas de la BD. |

## Errores y datos parciales

- JSON mal formado (por ejemplo, una coma final): HTTP 422 con `details.fields`.
- Errores de contrato explícitos: HTTP 422 con `details.reason` para facilitar el diagnóstico.
- Proveedor USIG no disponible: HTTP 502 con código genérico y `request_id` correlacionable.
- Esquema/consulta no disponible: HTTP 503, sin SQL ni trazas en el mensaje público.
- Dirección localizada pero parcela no encontrada: respuesta parcial con advertencias, no un error interno.
- Candidatos espaciales ambiguos: estado ambiguo, lista de candidatos y ninguna asignación arbitraria.

## Metadatos obligatorios al integrar el frontend

No descartar `request_id`, `warnings`, `sources`, `source_version_id`, versión, publisher, URL, checksum, fechas de vigencia y `metadata.ai_used`. Mostrar por separado contexto observacional (usos relevados) y regla normativa de compatibilidad.
