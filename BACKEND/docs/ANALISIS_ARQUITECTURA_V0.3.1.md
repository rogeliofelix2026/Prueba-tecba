# Revisión de arquitectura y cambios — SGI Backend v0.3.1

Fecha de revisión: 13/10/2026.

> Alcance: revisión del código fuente del paquete v0.3.0. El archivo `Sistema de Gestión Inteligente - TECBA.pdf` mencionado en la consulta no estaba incluido en el ZIP disponible, así que no afirmo haber verificado el PDF directamente. La evaluación de alineación con TECBA se basa solo en los criterios que acompañaron la consulta: IA como capa de interpretación y primacía de datos estructurados.

## Diagnóstico ejecutivo

La base es razonable para un MVP determinista y no necesita una reescritura ni microservicios. El camino principal ya está implementado en `POST /api/v1/territory`: el servicio coordina catálogo de actividad, geocodificación, parcela/SMP, contexto urbanístico, evaluación de reglas, Anexo II, detalles procedimentales, fuentes y advertencias. Esa ruta no invoca IA. PostgreSQL/PostGIS son la fuente estructurada para la evaluación territorial y el texto/RAG queda separado.

El ZIP original, sin embargo, no demuestra integración productiva por sí solo: en el entorno de esta revisión no estaban disponibles los drivers de PostgreSQL/pgvector, no se pudo conectar a Supabase/PostGIS y no se ejecutó la ingesta real. Además, el número de endpoints auxiliares hace fácil que el frontend elija accidentalmente una ruta incompleta o encadene llamadas innecesarias.

## Qué está bien diseñado

- **Orquestación determinista única:** la consulta normal no necesita llamar al endpoint de geocoding, luego a territorio, luego a evaluación y finalmente a trámites. El flujo completo se reúne en un servicio.
- **Separación de responsabilidades:** `api`, `services`, `repositories`, `integrations` e `ingestion` cumplen propósitos diferentes sin introducir una arquitectura distribuida innecesaria.
- **Resolución territorial conservadora:** el SMP tiene prioridad; una coincidencia espacial debe ser inequívoca, y una aproximación por proximidad no debería declararse `resolved` sin confirmación.
- **Geometría bajo demanda:** evitar incluir todos los polígonos en cada respuesta reduce el tamaño de las respuestas; se puede pedir cuando se visualice el mapa.
- **Fuente de verdad estructurada:** actividad, reglas, mixturas, distritos, mappings y metadatos vienen de los datos procesados, no de una respuesta inventada por el LLM.
- **Trazabilidad:** `request_id`, warnings, versiones de fuentes y auditoría de consultas son una buena base para explicar de dónde surge cada resultado.
- **Respuesta parcial explícita:** un faltante de una fuente debería producir `partial`/`insufficient_data`, no un resultado legal definitivo.

## Riesgos y brechas que siguen abiertos

| Área | Evaluación | Acción proporcional para MVP |
|---|---|---|
| Contrato API / 422 | Había ejemplos con coma final y campos no reconocidos podían quedar ignorados por el comportamiento por defecto de Pydantic. | Se endurecieron los modelos HTTP, se añadió ejemplo OpenAPI y se mejoró la pista del 422. El contrato real del navegador aún debe probarse. |
| Simplicidad de endpoints | Existen rutas redundantes de diagnóstico/compatibilidad, aunque ya hay un endpoint principal. | Documentar como ruta recomendada solo health, ready, activities, territory y mapa opcional. Mantener las otras rutas para no romper integraciones existentes. |
| Autenticación | No hay authN/authZ. Es aceptable solo en desarrollo o demo controlada. | Bloqueante antes de exposición pública: usar OIDC institucional (miBA si se habilita acceso), validar issuer/audience/firma/expiración y definir autorización. |
| Rate limiting | Los semáforos y límites de concurrencia son por proceso; no limitan globalmente a todas las réplicas. | Antes de tráfico público, incorporar limitación distribuida en gateway/infraestructura. No simular rate limit global con un contador local. |
| CORS/host de producción | Depende de configurar dominios reales; los defaults son para local. | Configurar `CORS_ORIGINS` y `ALLOWED_HOSTS` en el proveedor. No habilitar wildcard para resolver problemas del navegador. |
| Documentación pública | La configuración anterior activaba Swagger por defecto. | Cambiar el default a deshabilitado y habilitar `/docs` expresamente en el `.env` local. En producción confirmar `DOCS_ENABLED=false`. |
| Pool de base | `DB_MAX_SIZE` es por proceso; replicar la API multiplica conexiones. | Dimensionar `DB_MAX_SIZE × réplicas` contra el límite del proveedor y observar saturación/latencia. |
| Caché/USIG | Buen objetivo reducir llamadas repetidas; una coordinación local no garantiza single-flight entre diferentes réplicas. | Medir cache hit ratio y llamadas reales en staging; comprobar que la clave es normalizada y que los resultados parciales tienen TTL más corto. |
| Observabilidad | Hay request ID y logs de duración, pero faltan métricas operativas demostradas (latencia por dependencia, errores, saturación pool). | Empezar con logs estructurados + métricas básicas de API/DB/USIG antes de introducir una plataforma compleja. |
| RAG/LLM | El cliente de IA y las rutas heredadas pueden coexistir, pero no son necesarias para resolver el caso determinista. | Mantener el flujo principal independiente; implementar IA después de tener un conjunto estable de casos/fixtures y referencias verificables. |
| Datos normativos | Un mapping no garantiza que el detalle de un trámite esté cargado o vigente. | No mostrar detalle como completo si faltan requisitos/documentos/pasos; auditar vigencia y fuente con responsables funcionales. |
| Operación DB | El paquete contiene migraciones históricas, incluida una línea base destructiva según los documentos. | Ensayar cambios en una base descartable, revisar historial remoto y backups. Nunca usar `db reset --linked` como diagnóstico. |

## Cambios aplicados en v0.3.1

1. Se añadió un modelo base HTTP con `extra="forbid"`: un campo mal escrito ya no se ignora silenciosamente.
2. Se deshabilitaron números no finitos para el contrato y se rechazan direcciones/preguntas obligatorias compuestas solo por espacios.
3. Se añadió un ejemplo al esquema de OpenAPI para `POST /api/v1/territory`.
4. El 422 de entrada vacía incluye un código y las opciones esperadas; el manejador de validación da pistas por campo para JSON inválido, campos requeridos y campos desconocidos, sin devolver los valores ingresados.
5. Swagger/ReDoc queda deshabilitado por defecto; `.env.example` lo habilita solo para desarrollo local.
6. Se agregó un contrato de API simplificado, una matriz de pruebas funcionales/integración y pruebas unitarias del contrato de entrada.

## Qué no se cambió a propósito

- No se eliminaron las rutas auxiliares ni se cambiaron los nombres de respuesta, para evitar romper al frontend u otros clientes existentes.
- No se agregó rate limiting casero en memoria: no sería correcto entre varias réplicas.
- No se agregó autenticación inventada; debe integrarse con el proveedor institucional autorizado.
- No se ejecutaron migraciones, ingestas ni escrituras en la base real.
- No se movió RAG a la ruta determinista ni se permitió que la IA elija una actividad, parcela o trámite legal.

## Cómo avanzar

**Fase 1 — estabilizar el flujo determinista.** Corregir los errores de contrato detectados por el frontend; hacer pasar pruebas locales; luego `GET /ready`, `scripts/check_db.py` y `scripts/smoke_territory.py` contra staging. Cerrar el caso de aceptación con evidencia de cada fuente y el registro de auditoría.

**Fase 2 — calidad de datos y reglas.** Auditar cobertura de catálogo, mapping Anexo II, reglas por mixtura y procedimientos completos; revisar manualmente los mappings no confirmados. Agregar fixtures para actividad/dirección con salida esperada y ejecutar una regresión después de cada carga.

**Fase 3 — operación segura.** Configurar secretos, CORS/hosts, documentación, backups/PITR, restauración, rate limiting, autenticación institucional y métricas. Realizar pruebas de carga con conexiones contadas antes de aumentar réplicas.

**Fase 4 — IA como capa explicativa.** Definir un contexto estructurado inmutable para el modelo, recuperar evidencias normativas cuando se requieran, mostrar citas, controlar prompt injection y comparar respuestas asistidas contra los resultados deterministas. El modo IA no puede alterar el estado, la actividad resuelta, la parcela, la compatibilidad ni el trámite derivado por reglas.

## Validación de esta revisión

- `python -m compileall -q app ingestion scripts tests`: correcto tras los cambios.
- 25 pruebas enfocadas pasaron sin usar drivers de base. La suite completa pasó (**101 passed**) al inyectar stubs temporales externos solo para hacer importables módulos dependientes de `psycopg`/`pgvector`; no son parte del ZIP y no validan los drivers reales.
- Tres pruebas HTTP directas con ASGI transport verificaron JSON mal formado, campo desconocido y cuerpo vacío; las tres devuelven 422 con request ID y explicación segura.
- No se conectó a Supabase, no se ejecutaron migraciones ni se verificó el dataset remoto. El smoke real queda pendiente en el entorno de desarrollo/staging del equipo.
