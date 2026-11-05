# SGI Backend

Backend del MVP de Gestión Inteligente para InnovaLab.

Esta versión (0.3.5) prioriza el vertical slice territorial **determinista**: consulta inicial → actividad del catálogo → confirmación cuando corresponda → geocodificación USIG → parcela/SMP → información urbanística → reglas de uso → clasificación de trámite → respuesta estructurada y trazable.

La ruta `POST /api/v1/territory` a futuro podrá usar un intérprete de entrada si `AI_INPUT_INTERPRETER_ENABLED=true`; por defecto sigue desactivado. La etapa de explicación final continúa sin implementar y `AI_EXPLANATION_ENABLED` no se conecta al flujo en esta versión. La IA solo propone menciones: catálogo, geocodificación, resolución parcelaria, compatibilidad y clasificación de trámite siguen a cargo de servicios determinísticos. El endpoint heredado `/api/v1/queries` conserva capacidades adicionales y generación opcional; no es el contrato principal del vertical slice.


## Responsabilidades

1. API HTTP con FastAPI.
2. Geocodificación y datos complementarios mediante USIG.
3. Consulta territorial/procedimental con PostgreSQL + PostGIS.
4. Retrieval híbrido con PostgreSQL + pgvector + búsqueda léxica.
5. Generación opcional con Ollama local.
1. Ingesta separada de PDF, CSV/GIS y embeddings.

La ingesta no corre dentro de una request HTTP.

## Estructura

```text
backend/
├── app/
│   ├── api/            # endpoints + contratos HTTP
│   ├── core/           # configuración + pools DB + logging
│   ├── services/       # casos de uso / orquestación
│   ├── repositories/   # SQL y persistencia
│   ├── integrations/   # USIG + Ollama
│   └── rag/            # chunking + retrieval + generación
├── docs/  
└── scripts/            # utilidades manuales

```

## Instalación

Para el runtime únicamente, `uv sync` instala solo las dependencias obligatorias. Para desarrollo y tests agregá `dev`; para ingesta de PDF/GIS agregá `ingest`.

Con `uv`:

```bash
uv sync --extra dev --extra ingest
```

Con `pip`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,ingest]"
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`


## Estado y límites conocidos

- El esquema territorial guarda mixturas en `urban_parcel_rules.mixturas SMALLINT[]` y mantiene la geometría opcional en `parcel_geometries.geom`; `parcels` suele contener solo atributos en el pipeline normal. Durante una transición, los repositorios siguen reconociendo las columnas heredadas si la migración aún no se aplicó.
- La parcela se identifica primero por SMP. Si falta, se intenta contención inequívoca del punto en un polígono. Como último recurso, un candidato dentro de 35 m se expone con distancia y `confirmation_required=true` solo si aventaja al segundo candidato por al menos 4 m; ese resultado queda `partial`, nunca `resolved`, hasta confirmar la parcela.
- El valor `[]` en `mixturas` significa que el origen no informó mixturas utilizables; nunca se convierte en compatibilidad.
- El mapeo de Anexo II en `activity_tramite_mappings` es independiente de `activity_procedures`; si esta última está vacía o no existe, el backend intenta unir el tipo de trámite a `procedure_variants`. Los requisitos, documentos y pasos pueden seguir incompletos y la API lo informa.
- El corte del catálogo revisado contiene 325 actividades: 293 con tipo único, 2 mapeos condicionales y 30 sin correspondencia automática en el Anexo II. Esos 30 casos quedan pendientes de revisión normativa.
- Las pruebas locales no prueban la conexión, los permisos, PostGIS ni los datos reales de Supabase. Ejecutar `scripts/check_db.py` contra el entorno elegido antes de aceptar una carga.


## Estado actual v0.3.5: contrato, integridad e intérprete de entrada

### Contrato de `POST /api/v1/territory`

La respuesta incluye `contract_version: "1.2"`. El frontend debe leer `status`, `warnings`, `activity.status`, `location`, `territory.urbanism.status`, `compatibility`, `procedure_type_mapping` y `procedures.status`; no debe inferir éxito por la mera presencia de HTTP 200. Los estados parciales son resultados válidos y deben mostrarse con sus advertencias.

Estados funcionales principales observados en el flujo: `resolved`, `partial`, `needs_activity`, `needs_activity_confirmation`, `needs_address`; las subestructuras tienen sus propios estados como `available`, `unavailable`, `not_loaded`, `ambiguous` o `insufficient_data`. HTTP 4xx/5xx queda reservado para entrada inválida, dirección no encontrada o dependencia/servicio no disponible. Consultar `docs/API_TERRITORY_CONTRACT_v1.2.md` para la estructura y ejemplos.

`execution.ai_stages.input_interpreter` expone `enabled`, `status`, `used`, `called`, `candidate_count` y si se usó fallback. Sus estados incluyen `disabled`, `skipped`, `running`, `completed`, `completed_no_candidates` y `unavailable_fallback`. `execution.ai_stages.explanation_generator` continúa deshabilitado. `execution.mode` sigue siendo `deterministic`: las decisiones y validaciones de negocio no dependen del modelo. `execution.ai_used` indica si una extracción aceptada por el backend contribuyó al flujo.

### Códigos de trámite

La clasificación de Anexo II y el código de `procedure_variants.code` son conceptos distintos. La correspondencia conocida queda centralizada en `app/core/procedure_codes.py`:

| Código Anexo II | Código canónico de variante |
|---|---|
| `DDRR_CP` | `DDRR_CON_PLANO` |
| `DDRR_SP` | `DDRR_SIN_PLANO` |
| `LICENCIA` | `LICENCIA` |

`DDRR_E` no se convierte en una variante inventada: solo resolverá si existe una variante explícita con ese código o si se documenta una equivalencia oficial. Antes de aplicar cambios a la BD, revisar los códigos existentes y la procedencia/versionado del mapeo.

### Intérprete de entrada: configuración y comportamiento

El servicio `app/services/input_interpreter.py` solicita salida JSON a Ollama con formato estructurado. El bloque `query.input_interpretation` deja disponibles las menciones aceptadas y su evidencia para que el frontend entienda qué se interpretó sin confundirlo con un código oficial. Rechaza candidatos cuya mención/evidencia no aparece en el texto original. Las menciones de calle/altura deben poder parsearse; las superficies, anchos y frentes necesitan evidencia numérica y contexto semántico. Después, `TerritoryFlowService` valida los candidatos de actividad mediante `ActivityRepository`. Una coincidencia exacta validada desde lenguaje natural no equivale a una selección expresa del usuario: la respuesta mantiene `needs_activity_confirmation` cuando corresponde. Las coincidencias parciales solo se muestran como sugerencias.

Si Ollama no responde o su salida no cumple el contrato, se agrega `AI_INPUT_INTERPRETER_UNAVAILABLE` y se conserva la resolución determinística. No se envía información a servicios externos por defecto: el adaptador apunta a `OLLAMA_BASE_URL`, cuyo default es `http://127.0.0.1:11434`. En Render, `localhost` es el propio contenedor del backend y no un equipo del desarrollador; por eso el manifiesto mantiene la bandera apagada. Para activarla en staging/prod hace falta desplegar Ollama en una red privada autorizada y configurar ese endpoint explícitamente.

Para probarlo localmente:

```bash
# Terminal 1: iniciar Ollama local y descargar el modelo configurado
ollama serve
ollama pull qwen3:8b

# Terminal 2: entorno Python, base de datos y API ya configurados
# En .env:
AI_INPUT_INTERPRETER_ENABLED=true
AI_INPUT_INTERPRETER_TIMEOUT_SECONDS=12
AI_EXPLANATION_ENABLED=false
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=qwen3:8b

uvicorn app.main:app --reload
```

No habilitar el intérprete en producción hasta ejecutar la matriz QA del README en un entorno controlado. El apagado debe ser inmediato mediante `AI_INPUT_INTERPRETER_ENABLED=false`.

### Explicador final (fase posterior)

La segunda etapa redactará a partir de un resultado determinístico ya calculado, requisitos/pasos recuperados y fuentes versionadas. No puede alterar compatibilidad, clasificación ni requisitos; debe indicar datos faltantes y no convertir evidencia incompleta en certeza. `AI_EXPLANATION_ENABLED` permanece reservado/desconectado en v0.3.5.

### Integridad de datos: controles recomendados

- `urban_parcel_rules.parcel_id → parcels.id`: relación 0..1 regla urbanística por parcela (validar índice único/FK en el esquema real).
- `activity_aliases.activity_id → activities.id`; `activity_tramite_mappings.activity_id → activities.id` y `source_version_id → source_versions.id`.
- `procedure_variants.procedure_id → procedures.id`; requisitos, documentos y pasos se asocian al procedimiento mediante `procedure_id`; validar la cardinalidad real y la procedencia de cada fila.
- `parcel_geometries` se relaciona por parcela/SMP según el esquema vigente y debe conservar `source_version_id`; no cargar geometría sin fuente/versionado.
- Los cruces de tablas 1:N pueden duplicar filas. Consultar por etapas, agregar por clave o usar `EXISTS` cuando solo se necesite verificar existencia.
- Ejecutar primero los diagnósticos SQL de solo lectura. No aplicar `DROP`, baseline destructivo, `--reset` ni reparaciones automáticas sobre la BD remota sin respaldo y revisión explícita.

## Testing y QA

El resultado y las limitaciones de la validación de esta entrega están documentados en [`docs/QA_REPORT_V0.3.5.md`](docs/QA_REPORT_V0.3.5.md). La suite completa debe repetirse después de instalar las dependencias de desarrollo.

### Local

```bash
python -m pip install -r requirements-dev.txt
pytest -q
ruff check app tests
```

### Staging / base real (solo lectura antes de migrar)

1. Confirmar `DATABASE_URL` y entorno objetivo; no copiar secretos al repo ni a logs.
2. Ejecutar `python scripts/check_db.py` y los SQL de diagnóstico de integridad.
3. Comprobar que las variantes esperadas existen y que `DDRR_E` no se muestra como disponible si no tiene variante real.
4. Probar dirección no encontrada, actividad desconocida, actividad ambigua, ausencia de regla urbanística, usos no cargados, geometría ausente y fallo del proveedor/modelo.
5. Verificar que el frontend renderice `partial` y `warnings` sin confundirlos con una aprobación normativa.
6. Antes de cualquier migración, revisar el diff, el historial remoto, respaldo/PITR y el plan de rollback.

### Criterios de aceptación de esta fase

- La consulta determinista funciona con ambas banderas de IA apagadas.
- Los códigos de trámite se normalizan en un único módulo y tienen pruebas unitarias.
- La respuesta expone versión de contrato y estados de las etapas de IA sin declarar usos que no ocurrieron.
- No se pierde información de procedencia; una ausencia de datos se representa como parcial/no disponible, no como compatibilidad positiva.
- README, ejemplos API, pruebas y configuración coinciden.

### Próximas fases sugeridas

1. **Fase A — cierre de integridad:** contrastar constraints/índices con staging, códigos canónicos y source versions; el seed ya usa `DDRR_CON_PLANO`/`DDRR_SIN_PLANO`, mientras Anexo II conserva `DDRR_CP`/`DDRR_SP`.
2. **Fase B — contrato frontend:** validar `API_TERRITORY_CONTRACT_v1.2.md` y que el frontend gestione estados de aclaración, evidencias, warnings y errores HTTP.
3. **Fase C — endurecer intérprete IA:** probar Ollama real, carga/concurrencia, timeouts, model output drift, prompt injection, direcciones ambiguas y parámetros contradictorios.
4. **Fase D — explicación IA/RAG:** recuperación con citas/versiones, política de no responder sin evidencia, evaluación de factualidad y prompt-injection.
5. **Fase E — seguridad/operación:** autenticación/autorización según audiencia, rate limits, límites de payload, observabilidad sin datos sensibles, backup/restore y pruebas de carga.


### QA adicional del intérprete (v0.3.5)

Con `AI_INPUT_INTERPRETER_ENABLED=false`, la salida debe continuar por la ruta existente y `ai_used=false`. Con la bandera activa, comprobar al menos:

1. Actividad mencionada literalmente y coincidente con un alias oficial: se valida contra catálogo, pero sigue pendiente de confirmación si fue inferida del texto.
2. Actividad coloquial no catalogada exactamente (por ejemplo, “cafetería”): se muestran sugerencias, nunca se selecciona una equivalencia legal por similitud.
3. Texto sin mención de actividad/dirección: no se inventan candidatos; el estado solicita la información faltante.
4. Dirección mencionada: se valida como texto/evidencia y luego se geocodifica con USIG. Si USIG no la encuentra, no se da por válida.
5. Parámetro extraído: número presente en evidencia y contexto correcto (`superficie`, `ancho de calle` o `frente`); los valores no pueden pisar un valor explícito del request.
6. Respuesta JSON inválida, timeout, Ollama detenido o modelo inexistente: respuesta determinística continúa y aparece `AI_INPUT_INTERPRETER_UNAVAILABLE`.
7. Prompt injection dentro del texto: el modelo no puede cambiar rol, indicar reglas ni forzar selección de catálogo; toda salida sigue sometida a validación local.
8. Verificar `execution.ai_stages.input_interpreter` y que `execution.ai_used` solo sea `true` cuando un candidato aceptado haya contribuido al flujo.

Pruebas aisladas del intérprete: `pytest -q tests/test_input_interpreter.py`. Pruebas de integración determinística con fakes: `pytest -q tests/test_territory_flow.py`. Para la suite completa instalar dependencias del proyecto con `python -m pip install -r requirements-dev.txt` dentro del entorno virtual.

## Arquitectura

```text
app/api          contratos HTTP y manejo de errores
app/services     flujo de aplicación y evaluación determinista
app/repositories SQL, lectura de esquema/capacidades y procedencia
app/integrations USIG y cliente de IA para endpoints fuera del flujo determinista
app/rag          recuperación/generación opcional
app/core         configuración, conexiones y normalizaciones compartidas
ingestion        procesos offline y de datos
supabase/migrations  único historial canónico de migraciones
scripts          preflight de migraciones, auditoría read-only y utilidades
```

No se ejecutan ingestas desde una request HTTP. Los scripts transaccionales deben probarse con `--dry-run` y una muestra antes de una carga completa.

## Instalación local

Requiere Python 3.11+ y PostgreSQL con PostGIS. pgvector se necesita para RAG/embeddings, no para la evaluación territorial determinista.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
```

Completar `DATABASE_URL` en `.env`. No agregar `.env`, claves de Supabase ni credenciales al repositorio.

## Seguridad de migraciones — leer antes de tocar la BD

Para reconstruir un entorno desde cero, seguir `docs/RECONSTRUCCION_LIMPIA_SEGURA.md`. No vaciar manualmente el esquema remoto conservando un historial de migraciones que dice que ya se aplicaron.

`supabase/migrations` es el **único árbol canónico**. El baseline `20261008100000_schema_mvp_final.sql` contiene `DROP TABLE ... CASCADE`; está destinado a inicializar un esquema reconstruible y **no debe ejecutarse de nuevo sobre la base cargada**. Eliminar duplicados del repositorio no significa borrar ni reescribir el historial de Supabase.

```bash
python scripts/migrate.py        # inventario local; solo lectura, no aplica SQL
supabase migration list --linked # revisar el historial remoto
python scripts/check_db.py       # auditar esquema/capacidades: solo lectura
```

Solo después de confirmar que todo baseline destructivo ya está asentado en el historial remoto, evaluar si hay migraciones incrementales pendientes y utilizar Supabase CLI. No ejecutar migraciones manualmente con `psql`, no utilizar `--reset` y no aplicar el baseline sobre datos cargados.

## API del vertical slice

Para el camino feliz del frontend alcanza con `GET /api/v1/activities?search=...`, una llamada a `POST /api/v1/territory` y, cuando se dibuja un polígono, `GET /api/v1/map/parcel/{smp}`. No es necesario encadenar geocoding, consulta territorial, evaluación y trámites manualmente. El resto de las rutas se mantiene como soporte o compatibilidad.

| Método | Ruta | Responsabilidad |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness |
| `GET` | `/api/v1/ready` | Conexión + capacidades mínimas de esquema |
| `GET` | `/api/v1/activities` | Catálogo/autocomplete de rubros oficiales |
| `POST` | `/api/v1/territory` | Flujo inicial completo, determinista |
| `POST` | `/api/v1/geocoding` | Geocodificación y metadatos de USIG |
| `GET` | `/api/v1/territory` | Compatibilidad anterior (marcado deprecated en OpenAPI): SMP o coordenadas |
| `POST` | `/api/v1/territory/evaluate` | Compatibilidad avanzada (deprecated en OpenAPI) |
| `GET` | `/api/v1/map/parcel/{smp}` | Feature GeoJSON de una parcela si hay geometría |
| `GET` | `/api/v1/context/parcel/{smp}` | Contexto territorial por SMP |
| `GET` | `/api/v1/activities/{activity_id}/procedures` | Clasificación Anexo II y detalles procedimentales disponibles |
| `POST` | `/api/v1/queries` | Flujo legado; puede habilitar RAG/IA por request |

Documentación interactiva: `/docs`, si `DOCS_ENABLED=true`.

Contrato simplificado vigente para el frontend: [`docs/API_SIMPLE_v1.md`](docs/API_SIMPLE_v1.md). La versión de compatibilidad anterior queda en [`docs/API_SIMPLE_V0.3.4.md`](docs/API_SIMPLE_V0.3.4.md). Diagnóstico del contrato flexible: [`docs/FIX_422_INPUT_CONTRACT.md`](docs/FIX_422_INPUT_CONTRACT.md). Plan de pruebas: [`docs/TEST_PLAN_FLUJO_V0.3.4.md`](docs/TEST_PLAN_FLUJO_V0.3.4.md). Cambios recientes: [`docs/CHANGELOG_V0.3.4.md`](docs/CHANGELOG_V0.3.4.md). Diagnóstico general SQL: [`docs/sql/diagnostico_integridad_flujo.sql`](docs/sql/diagnostico_integridad_flujo.sql). Diagnóstico específico del flujo real: [`docs/sql/diagnostico_siguiente_paso_v033.sql`](docs/sql/diagnostico_siguiente_paso_v033.sql). Política de caché de geometrías: [`docs/GEOMETRY_CACHE_POLICY.md`](docs/GEOMETRY_CACHE_POLICY.md).

### Ejemplo de consulta inicial

El contrato recomendado para el flujo determinista es simple: `activity` + `address`. El Frontend puede usar `GET /api/v1/activities?search=...` como autocompletado del catálogo, pero el usuario no necesita conocer ni escribir el código interno. Se acepta `activity_code` como selección opcional para integraciones o para desambiguar, pero si se manda junto con `activity` ambos deben coincidir con el mismo registro. `query` queda como compatibilidad para input en lenguaje natural.

```http
POST /api/v1/territory
Content-Type: application/json

{
  "activity": "Cafetería",
  "address": "Corrientes 2500",
  "surface_m2": 180,
  "include_geometry": true
}
```

`include_geometry` es `false` por defecto para no serializar polígonos grandes en cada respuesta. Pedir el polígono de forma explícita o usar `/api/v1/map/parcel/{smp}` cuando la UI realmente vaya a dibujarlo.

Si el rubro se reconoce dentro del texto pero hay varios candidatos, la API devuelve `needs_activity_confirmation` con los candidatos. Para continuar, alcanza con repetir con el nombre oficial elegido en `activity`; `activity_code` sigue siendo opcional. Si el texto no alcanza para resolver la dirección, enviar `address` por separado.

Estados del flujo: `needs_activity`, `needs_activity_confirmation`, `needs_address`, `partial` y `resolved`. `partial` no significa “no permitido”: indica que faltan datos o que una parte del flujo requiere revisión. La evaluación distingue `compatible`, `conditional`, `council_review`, `not_compatible` e `insufficient_data`.

La respuesta incluye `request_id`, entrada/extracción, actividad y método de resolución, localización, parcela, barrio/comuna, mixturas, distritos especiales, observaciones de usos, compatibilidad, mapeo de trámite, procedimientos cargados, `source_version_id`, versiones/checksum/URLs, advertencias y `metadata.ai_used=false`.

## Resolución completa de la consulta (v0.3.4)

- `docs/ANALISIS_FLUJO_V0.3.4.md`: causas de campos vacíos, contratos de datos y límites reales de las fuentes.
- `docs/varios/GEOMETRY_CACHE_POLICY.md`: fuente oficial de polígonos, configuración de caché lazy y procedencia.
- `docs/sql/20261013140000_mvp_flow_completion.sql`: migración idempotente de alias provisional y detalles de modalidad exprés.
- `docs/sql/diagnostico_v034_flujo_completo.sql`: validaciones de sólo lectura para parcela, actividad, trámite, geometría y RUS.

**Geometría:** USIG determina coordenadas y SMP, pero los endpoints públicos documentados no devuelven el polígono parcelario. Para cachear geometría al consultar una parcela, hay que descargar la fuente oficial Parcelas, convertirla preferentemente a GeoPackage con índice en `smp`, y configurar `PARCEL_GEOMETRY_SOURCE_PATH`, `PARCEL_GEOMETRY_SOURCE_LAYER` y `PARCEL_GEOMETRY_SOURCE_VERSION_ID` (ID de `source_versions` correspondiente a ese archivo, no un ID supuesto). No se importan automáticamente todas las geometrías.


# > TRABAJO DEL ÁREA <

El área **Backend** será responsable del desarrollo de los servicios y lógica necesaria para el funcionamiento del Sistema de Gestión Inteligente.

El trabajo inicial incluye:

* Diseñar e implementar los servicios necesarios para el MVP.
* Procesar las solicitudes realizadas desde el frontend.
* Gestionar la información utilizada por el sistema.
* Implementar las integraciones necesarias con las fuentes de información definidas.
* Proporcionar los servicios que necesite el Frontend.
* Participar en la integración del flujo completo del MVP.

La arquitectura y las tecnologías definitivas del Backend se irán definiendo durante el desarrollo del proyecto.

---

## Trabajo con GitHub desde VS Code

Cada integrante debe trabajar en su **rama**, evitando realizar cambios directamente sobre `main`.

### 1. Actualizar el proyecto

Abrir el proyecto en VS Code y abrir:

**Terminal → New Terminal**

```bash
git checkout main
git pull origin main
```

### 2. Ir a la rama de Backend

```bash
git checkout backend
```

Si la rama todavía no existe:

```bash
git checkout -b backend
git push -u origin backend
```

### 3. Realizar el trabajo

Modificar o agregar los archivos correspondientes al área Backend.

### 4. Revisar los cambios

```bash
git status
```

### 5. Guardar los cambios

```bash
git add .
git commit -m "Descripción breve del cambio"
```

Ejemplo:

```bash
git commit -m "Agrega servicio inicial del MVP"
```

### 6. Subir los cambios

```bash
git push origin backend
```

### 7. Crear Pull Request

Desde GitHub:

**Pull requests → New pull request**

Seleccionar:

```text
base: main
compare: backend
```

Agregar una breve descripción de los cambios y crear el Pull Request.

### 8. Integración

El cambio será revisado por el equipo y, una vez aprobado, se integrará a `main`.

**No realizar Push directamente sobre `main`.**