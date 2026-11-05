# SGI — contrato simple para Frontend (API v1)

**Versión del backend:** 0.3.5 (staging)  
**Base URL:** la URL HTTPS entregada por Render. No hardcodear localhost.  
**Formato:** JSON UTF-8. La API no requiere que el navegador se conecte directamente a PostgreSQL/Supabase.

## 1. Qué integra el Frontend

Para el camino feliz se recomienda este orden:

1. `GET /api/v1/activities?search=...` para el autocompletado opcional del catálogo.
2. `POST /api/v1/territory` con actividad y dirección para realizar una única resolución integrada.
3. Mostrar los resultados según el `status`, `warnings` y `trace`; conservar `request_id`.
4. Mostrar el marcador con `location.latitude` y `location.longitude`. El polígono solo debe mostrarse cuando la respuesta incluye una geometría real.

No encadenar manualmente geocoding → parcela → mixtura → procedimiento. El endpoint principal coordina ese flujo.

## 2. Variables de entorno del Frontend

### React + Vite

```dotenv
VITE_SGI_API_BASE_URL=https://<dominio-real-del-backend>
```

### Next.js (variable pública consumida desde el navegador)

```dotenv
NEXT_PUBLIC_SGI_API_BASE_URL=https://<dominio-real-del-backend>
```

El valor no debe acabar con `/`. Nunca colocar `DATABASE_URL`, passwords, claves `service_role` ni secretos del servidor en variables `VITE_*` o `NEXT_PUBLIC_*`.

## 3. Endpoints recomendados

| Método | Ruta | Uso | Notas |
|---|---|---|---|
| `GET` | `/api/v1/health` | Liveness del proceso | No demuestra conectividad a la base. |
| `GET` | `/api/v1/ready` | Readiness + capacidades del esquema | Interpretar también `degraded` y `degraded_capabilities`. |
| `GET` | `/api/v1/activities?search=cafe&limit=20&offset=0` | Catálogo/autocomplete | `search`, `limit` (1–100) y `offset` son opcionales. |
| `POST` | `/api/v1/territory` | Consulta integrada inicial | Endpoint principal del MVP. |
| `GET` | `/api/v1/map/parcel/{smp}` | Feature GeoJSON parcelario | Si falta geometría, puede devolver `geometry: null` y `status: partial`. |
| `GET` | `/api/v1/context/parcel/{smp}` | Contexto de una parcela resuelta | Útil si el Frontend necesita recargar el panel territorial por SMP. |
| `GET` | `/api/v1/activities/{activity_id}/procedures` | Detalle de actividad/trámite | No suele ser necesario para el flujo inicial; la respuesta principal ya incluye procedimientos. |

Rutas auxiliares/compatibilidad (`POST /api/v1/geocoding`, `GET /api/v1/territory`, `POST /api/v1/territory/evaluate`, `POST /api/v1/queries`) no deben ser el camino principal del nuevo Frontend. `POST /api/v1/queries` es una ruta heredada que puede acceder a funciones RAG/IA; `RAG_ENABLED=false` en staging.

## 4. Request principal

`POST /api/v1/territory`

Headers:

```http
Content-Type: application/json
```

Cuerpo mínimo recomendado con campos separados:

```json
{
  "activity": "Alimentación en general y gastronomía",
  "activity_code": "1.5",
  "address": "Corrientes 2500"
}
```

Cuerpo ampliado:

```json
{
  "activity": "Alimentación en general y gastronomía",
  "activity_code": "1.5",
  "address": "Corrientes 2500",
  "surface_m2": 80,
  "street_width_m": null,
  "frontage_m": null,
  "include_geometry": false,
  "confirm_activity": true
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `activity` | string | En el camino feliz, sí | Nombre que el usuario eligió del catálogo. |
| `activity_code` | string | No | Código canónico si el selector ya lo conoce. Si se manda junto con `activity`, ambos deben corresponder a la misma actividad. |
| `address` | string | En el camino feliz, sí | Dirección dentro de CABA. |
| `query` | string | No | Alternativa de texto libre para el parser del backend. Para campos separados, preferir `activity` + `address`. |
| `surface_m2` | number positivo | No | Superficie del local, si la conoce el usuario. |
| `street_width_m` | number positivo | No | Dato contextual cuando esté disponible. No estimarlo en el Frontend. |
| `frontage_m` | number positivo | No | Dato contextual cuando esté disponible. No estimarlo en el Frontend. |
| `include_geometry` | boolean | No; default `false` | Solicita geometría parcelaria si existe en el backend. La respuesta no garantiza que la fuente geométrica esté configurada. |
| `confirm_activity` | boolean | No; default `false` | Confirma una actividad provisional si el backend la soporta para ese caso. También se puede reenviar el nombre canónico y `activity_code` elegido en el catálogo. |

El modelo ignora campos extra del formulario para favorecer compatibilidad, pero el Frontend debe enviar únicamente campos documentados.

## 5. Buscar actividades

`GET /api/v1/activities?search=cafe&limit=20&offset=0`

Ejemplo de estructura de respuesta (los datos exactos dependen del catálogo cargado):

```json
{
  "items": [
    {
      "id": 10,
      "code": "1.5",
      "name": "Alimentación en general y gastronomía",
      "category": "Comercial"
    }
  ],
  "status": "available",
  "sources": [],
  "request_id": "<uuid>",
  "generated_at": "<timestamp ISO-8601>"
}
```

Tratar el contenido de `items` como fuente de opciones; no inferir ni inventar códigos de actividad en el Frontend. No mostrar la actividad como confirmada solo porque coincide por alias o semejanza textual.

## 6. Cómo interpretar `POST /api/v1/territory`

La respuesta contiene, cuando esos datos están disponibles:

- `request_id`, `generated_at`, `query` y `execution`.
- `activity`: catálogo, código, método de resolución y si necesita confirmación.
- `location`: dirección normalizada, latitud/longitud, SMP y metadatos de USIG.
- `territory`: parcela, barrio/comuna, urbanismo, distritos especiales, datos útiles y calles adyacentes.
- `compatibility`: resultado determinista, mixturas consideradas, notas, datos de entrada y referencia de reglas.
- `procedure_type_mapping` y `procedures`: tipo de trámite, requisitos, documentos, pasos y variantes que estén realmente cargados.
- `sources`: URLs, publicador, versión, checksum y fechas si la fuente los informa.
- `warnings`, `metadata` y `trace`.

### Estados funcionales

| Estado | Comportamiento esperado de la UI |
|---|---|
| `needs_activity` | Pedir que el usuario elija un rubro del catálogo. |
| `needs_activity_confirmation` | Mostrar la actividad sugerida y solicitar confirmación; la compatibilidad es una vista previa. |
| `needs_address` | Pedir o corregir la dirección. |
| `partial` | Mostrar lo obtenido junto a lo que falta; no comunicar “no permitido” a partir de datos incompletos. |
| `resolved` | Se resolvieron los elementos principales del caso; sigue siendo orientación informativa, no autorización legal. |

HTTP `200` es compatible con un estado funcional parcial. Para decidir cómo presentar la pantalla hay que comprobar `status`, `warnings`, `activity.confirmation_required`, `compatibility.activity_confirmation_required`, `procedures.status` y `trace.persistence_status`.

### Regla para compatibilidad

Nunca presentar `compatibility.status: "compatible"` como una garantía de habilitación. Si `activity.confirmation_required` o `compatibility.activity_confirmation_required` es `true`, etiquetar el resultado como preliminar y pedir confirmación. Los requisitos/documentos marcados `conditional: true` deben conservar esa condición en la UI.

### Trazabilidad

Mostrar o permitir desplegar el origen del contenido con `sources` y `source_version_id`. No combinar datos de fuentes diferentes sin conservar el origen de cada bloque. `trace.persistence_status` debe ser `stored` para considerar completa la escritura de auditoría; `stored_partial` o `unavailable` deben tratarse como un estado operativo degradado, aunque la consulta pueda tener datos para mostrar.

## 7. Mapa

- Marcador: usar `location.latitude` y `location.longitude` cuando sean números válidos.
- Texto de dirección: usar `location.address_normalized` para mostrar la normalizada y conservar `address_input` como entrada del usuario si se necesita mostrar ambas.
- Enlace externo: `location.usig_map_url`, cuando exista, es una alternativa de navegación.
- Polígono: solo dibujar `geometry` si es un objeto GeoJSON real; puede llegar como `null`. `geometry_status: "source_not_configured"` no significa que la parcela no exista, sino que la API no pudo obtener su contorno desde una fuente configurada.
- Ciudad 3D: ofrecer un enlace externo como apoyo informativo. No interpretar el HTML de Ciudad 3D como GeoJSON propio ni asumir que su sitio se puede embeber o que dispone de un deep-link público estable sin verificarlo.

La falta de polígono no debe impedir mostrar el marcador, el contexto territorial y los datos de compatibilidad.

## 8. Errores HTTP

Formato habitual:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Hay campos faltantes o inválidos en la solicitud.",
    "request_id": "<uuid>",
    "details": { "fields": [] }
  }
}
```

| HTTP | Significado | Acción de UI |
|---|---|---|
| `400` | Solicitud o `X-Request-ID` inválido | Corregir request; no reintentar igual. |
| `404` | Recurso/dirección/parcela no encontrada según endpoint | Permitir corregir búsqueda; revisar `error.code`. |
| `413` | Request demasiado grande | Reducir contenido enviado. |
| `422` | Validación | Marcar campos señalados en `error.details.fields`. |
| `429` | Peticiones limitadas si una capa de rate limiting está habilitada | Informar y reintentar con espera. La app no debe depender de que exista hoy un limitador global. |
| `502` | Proveedor externo no respondió correctamente | Mostrar error recuperable y ofrecer reintento. |
| `503` | Base/esquema/proveedor/capacidad no disponible | Informar indisponibilidad; conservar el `request_id` para soporte. |
| `500` | Error interno inesperado | Mensaje genérico y referencia por `request_id`; no mostrar stack traces. |

La API incluye los headers `X-Request-ID` y `X-Process-Time-ms` en respuestas HTTP normales. El handler de errores intenta devolver un `request_id` también dentro de `error`.

## 9. Límite de responsabilidad

SGI ofrece una orientación preliminar construida desde las fuentes disponibles. No emite permisos, certificados ni decisiones vinculantes de la Ciudad. Los datos oficiales pueden tener fechas de corte; mostrar sus fuentes y advertencias, y derivar al enlace oficial cuando corresponda.
