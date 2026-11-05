# SGI — Matriz de pruebas y aceptación de v0.2.0

**Objetivo:** probar el camino determinista sin IA y fijar una puerta de release verificable. Los casos que requieran un valor real (SMP, regla, procedimiento, geometría) deben completar sus fixtures con resultados confirmados contra BD/fuente; no se dejan aserciones vagas ni valores inventados.

## 1. Puertas obligatorias para release

- [ ] Instalación desde cero desde el paquete y variables de entorno documentadas.
- [ ] Migración limpia en base vacía y prueba de upgrade en una base de prueba con datos de fixture.
- [ ] Tests unitarios del catálogo/aliases, parser de reglas y evaluación.
- [ ] Tests de contrato para `/territory` y `/queries` validados contra OpenAPI.
- [ ] E2E determinista: `question + activity + address` → ubicación → parcela → urbanismo → procedimientos → fuentes.
- [ ] Pruebas confirman cero invocaciones a Ollama/LLM y que `answer` puede permanecer `null` en v0.3.
- [ ] Cada resultado normativo procede de una regla versionada y muestra si depende de datos faltantes.
- [ ] Geometría opcional válida para una sola parcela, o warning con fallback al pin.
- [ ] Fuentes/versiones/fechas comprobadas; lo no disponible se declara como tal.
- [ ] Errores de proveedor, falta de datos y actividad desconocida no rompen ni falsean el resultado.
- [ ] Suite definida como unitaria/integración/E2E, con dependencias externas explicitadas.
- [ ] Sin bugs P0/P1 abiertos; limitaciones conocidas en release notes.

## 2. Casos de contrato territorial

| ID | Escenario | Entrada/fixture | Resultado esperado |
|---|---|---|---|
| TER-01 | Dirección conocida con SMP válido | Fixture USIG + parcela conocida | `200`, `resolved`; SMP canónico, coords y método `usig_smp`; metadatos de fuente. |
| TER-02 | Geocoding correcto, sin parcela local | Fixture con coords y sin polígono que la cubra | `200`, `partial`; coords se conservan y warning `PARCEL_NOT_RESOLVED`. |
| TER-03 | No se localiza la dirección | USIG devuelve sin resultado | Error 404 `ADDRESS_NOT_FOUND`; no fabricar coordenadas. |
| TER-04 | Proveedor caído/timeout | USIG mock lanza error de disponibilidad | 503 `GEOCODING_UNAVAILABLE`; distinto de dirección inexistente. |
| TER-05 | Request sin dirección/entrada inválida | Body vacío o dirección fuera del esquema | 422 `INVALID_REQUEST`. |
| TER-06 | Coordenadas incompletas en el alias GET | Falta lat o lon | 422; nunca consultar PostGIS con una pareja incompleta. |
| TER-07 | Parcela sin reglas urbanísticas | Parcela válida, 0 reglas | Parcela `resolved`; urbanism `unavailable`; warning. No afirmar “sin restricciones”. |
| TER-08 | Geometría solicitada | `include_geometry=true`, fixture parcela | GeoJSON `Polygon`/`MultiPolygon` válido EPSG:4326, solo la parcela. |
| TER-09 | Geometría omitida | `include_geometry=false` | `geometry=null` + comportamiento de warning documentado; coords para pin disponibles. |
| TER-10 | Punto/correspondencia ambigua | Fixture con 2 parcelas candidatas | `partial`/warning de ambigüedad; nunca seleccionar con `LIMIT 1` arbitrario. |
| TER-11 | Dirección fuera de CABA | Fixture geocoding fuera del límite | Estado/código documentado `ADDRESS_OUTSIDE_CABA`. |
| TER-12 | Datos administrativos ausentes | Parcela sin barrio/comuna relacionado | Parcel/urbanism no se pierden; objetos administrativos `null` y warning si es relevante. |
| TER-13 | Alias de GET mantiene consumidores | Query SMP heredada | Adaptador funciona durante transición, responde con contrato canónico o deprecation claramente documentada. |
| TER-14 | CORS Front | Origen permitido y no permitido | Origen permitido opera; otros no reciben cabeceras CORS abiertas por defecto. |
| TER-15 | Respuesta OpenAPI | Inspección `/openapi.json` | Modelos/nullable/enums coinciden con DTO y mocks. |

## 3. Casos de actividad y reglas

| ID | Escenario | Resultado esperado |
|---|---|---|
| ACT-01 | Nombre canónico exacto | Resuelve una actividad única y guarda ID/código oficial. |
| ACT-02 | Alias aprobado “cafetería” | Resuelve a la actividad revisada para el piloto con trazabilidad del alias. |
| ACT-03 | Actividad desconocida | `ACTIVITY_UNKNOWN`; no fuzzy match silencioso. |
| ACT-04 | Alias ambiguo | `ACTIVITY_AMBIGUOUS` y solicita desambiguación. |
| RULE-01 | `SI` / compatible básico | Estado coincide con regla y versión confirmadas. |
| RULE-02 | `NO` o `NPC` | Estado no compatible según diccionario normativo validado. |
| RULE-03 | `C` / `SCPC` | Interpretación condicional o consejo/revisión solo según diccionario oficial acordado. |
| RULE-04 | `SA` como condición alternativa | Verificar la semántica OR de fuente; pasar un caso donde el límite se supera pero la alternativa se cumple. No tratar ambas condiciones como AND. |
| RULE-05 | Sufijo `B` | Confirmar si es mínimo de superficie, límite de frente u otra condición según el código real; comprobar campos estructurados, no solo texto. |
| RULE-06 | `AMP12` | Validar con fuente qué dimensión aplica y que el seed persista los campos estructurados cuando corresponda. |
| RULE-07 | Límite con medida desconocida | Resultado condicional/insuficiente; no reemplazar la falta de dato con un supuesto. |
| RULE-08 | Tres mixturas/varias reglas | Orden, selección de regla y lógica de alternativa documentados; no elegir automáticamente la más favorable sin criterio validado. |
| RULE-09 | Distrito especial | Se aplica únicamente la consecuencia confirmada por normativa; hay referencia a fuente/distrito. |
| RULE-10 | Regla/mixtura no cargada | `unavailable`/partial y source warning; no es igual a prohibición. |

## 4. Casos del agregador y procedimientos

| ID | Escenario | Resultado esperado |
|---|---|---|
| QRY-01 | Camino feliz piloto | Un `POST /queries` devuelve contexto, actividad canónica, ubicación, territorio, evaluación, procedimientos y fuentes disponibles. |
| QRY-02 | Sin llamada de IA | Espiar/mockear clientes Ollama; con `generate_answer=false`, `retrieve_evidence=false` el número de invocaciones es 0. |
| QRY-03 | Geometría solicitada desde queries | `include_geometry=true` llega a `TerritoryService` y contiene solo la parcela. |
| QRY-04 | Geometría no solicitada | No se ejecuta consulta GeoJSON costosa o se devuelve `null`, conforme política publicada. |
| QRY-05 | Procedimientos disponibles | Procedimiento relacionado con la actividad incluye requisitos/documentos/pasos en orden, fuente/versionado y enlaces. |
| QRY-06 | Sin procedimientos | Resultado parcial con `PROCEDURES_UNAVAILABLE`; no muestra “sin trámites”. |
| QRY-07 | Datos procedimentales parciales | Muestra solo datos respaldados y advierte qué bloque falta. |
| QRY-08 | Una fuente secundaria falla | El resto del contexto útil se conserva con estado parcial; no se marca globalmente “no encontrado”. |
| QRY-09 | Dirección ausente cuando es requerida por el caso | Error/validación acordada; nunca inventa ubicación. |
| QRY-10 | Consulta/actividad/address no coinciden | Conserva originales y comunica el campo estructurado usado; no modifica silenciosamente la intención. |
| QRY-11 | Repetibilidad | Dos runs con fixtures/snapshots iguales producen igualdad de campos estructurados, excepto IDs/timestamps técnicos documentados. |
| QRY-12 | Trazabilidad | Cada bloque territorial/normativo/procedimental muestra fuente relevante, no solo una lista global opaca. |

## 5. Casos de reproducibilidad y operación

| ID | Escenario | Resultado esperado |
|---|---|---|
| OPS-01 | Instalar en entorno limpio | La guía instala dependencias; import y ejecución FastAPI funcionan. |
| OPS-02 | Migración desde cero | Todas las migraciones canónicas aplican en orden y sin SQL ausente. |
| OPS-03 | Migración/seed repetible | Re-ejecutar el camino soportado no duplica registros ni altera checksum de forma inesperada. |
| OPS-04 | `ready` sin DB | 503 normalizado, no filtra excepciones. |
| OPS-05 | Variables de entorno faltantes | Startup falla con mensaje útil; no aparecen secretos ni defaults inseguros inadvertidos. |
| OPS-06 | Versión de release | `health.version`, paquete y release notes informan `0.3.0` de forma consistente. |
| OPS-07 | Suite separada | Unit tests no dependen de USIG/Postgres real; integración externa se puede invocar por separado. |
| OPS-08 | Logs por request | `request_id`, tiempos y códigos de status/warning; sin payload crudo/secretos innecesarios. |

## 6. Fixtures de referencia requeridos

Antes de marcar verde, el equipo deberá completar en un archivo fixture versionado para cada caso:

- dirección exacta de entrada, respuesta normalizada de USIG (o mock fijado), coordenadas y SMP confirmado;
- ID de parcela canónica, barrio/comuna, geometría esperada (o hash/propiedades espaciales relevantes);
- versión/checksum de capas y reglas cargadas;
- actividad ID/código y alias aprobado;
- reglas crudas del Cuadro 3.3, interpretación validada y resultado esperado con datos explícitos;
- procedimiento oficial, requisitos/documentos/pasos y su fuente cuando se pruebe el camino completo;
- advertencias esperadas y bloques que deben quedar parciales.

No escribir en los fixtures una dirección geocodificada o un resultado de compatibilidad basándose exclusivamente en el mapa demo. Verificar contra la fuente original y la instancia PostGIS objetivo.

## 7. Plantilla de reporte por ejecución

- Commit/versión: `...`
- Base/snapshot: `...`
- Suite/command: `...`
- Unit: `n passed / n failed`
- Contract: `n passed / n failed`
- Integration: `n passed / n skipped / n failed`
- E2E determinista: `pass/fail`
- Llamadas LLM observadas: `0` requerido
- Fuentes/procedimientos validados: `...`
- Bugs P0/P1 abiertos: `0` requerido
- Limitaciones conocidas: `...`
- Aprobación Front/Backend/Data-QA: `...`
