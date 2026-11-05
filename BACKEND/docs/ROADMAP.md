# Evaluación y roadmap — SGI Backend v0.3.0

## 1. Objetivo de esta versión

Cerrar el **primer vertical slice territorial de punta a punta de forma determinista y sin IA**. A partir de la consulta inicial, el backend debe pedir la confirmación necesaria, resolver dirección/parcela, cruzar el territorio con las reglas de uso de la actividad, clasificar el trámite con base en el Anexo II y devolver un contrato común, versionado y explicable por datos/fuentes.

La versión no debe confundirse con el motor normativo completo: los resultados son preliminares y una clasificación de trámite no equivale a que los requisitos, pasos y documentos estén cargados.

## 2. Estado evaluado

### Capacidades que se incorporan al vertical slice

1. Resolución de actividad a partir de código, nombre o alias explícitos del catálogo. No usa embeddings ni similitud difusa; ambigüedades generan una respuesta que pide elegir/confirmar.
2. Extracción conservadora de calle y altura en consulta natural, con dirección explícita como prioridad.
3. Normalización compartida de SMP a sección de tres dígitos, conservando sufijos catastrales.
4. Resolución de parcela por SMP; el fallback espacial solo acepta contención inequívoca en geometría, no asigna la parcela más cercana.
5. Consulta adaptativa para el modelo compacto (`mixturas[]` + caché de geometría) y el modelo legacy (`uso_1/2/3` o geometría en `parcels`).
6. Consulta de barrio/comuna, indicadores, distritos especiales, observaciones de uso y procedencia.
7. Evaluación determinista por cada mixtura disponible y por reglas de `activity_use_rules`, incluyendo condiciones conocidas de superficie, frente/ancho y revisión del Consejo.
8. Clasificación actividad → tipo de trámite del Anexo II con estado por fila, unión por código de actividad, y metadatos de fuente.
9. Respuesta estructurada, advertencias estables, `request_id`, `source_version_id`, checksum, URL y fechas disponibles; el endpoint principal marca `ai_used=false`.
10. Endpoints específicos para mapa, contexto territorial y trámites, manteniendo rutas anteriores como compatibilidad.

### Estado de datos según la auditoría compartida

Los conteos siguientes son el snapshot de la auditoría y de las salidas de ingesta compartidas, **no una lectura nueva de Supabase**:

| Dato | Resultado auditado |
|---|---:|
| Registros en CSV del Código Urbanístico | 318.127 |
| Actividades del catálogo | 325 |
| Reglas actividad–mixtura | 1.300 |
| Parcelas con geometría/atributos según auditoría previa | 318.046 |
| Parcelas con regla urbana según auditoría previa | 249.393 |
| Filas de distritos especiales | 74.259 |
| Parcelas distintas en distritos especiales | 72.851 |
| SMP sin coincidencia en `parcels` en una ejecución de ingesta | 233 |
| Mapeo Anexo II: tipo único confirmado | 293 |
| Mapeo Anexo II: casos condicionales | 2 |
| Mapeo Anexo II: sin correspondencia automática | 30 |
| Tablas de detalle de procedimientos/requisitos/documentos/pasos | Sin filas en auditoría previa |

**Importante:** las diferencias entre 318.127 filas de fuente y 318.046 parcelas locales son señal de conciliación pendiente, no un motivo para crear parcelas ausentes con datos inferidos. Los 233 SMP deben quedar en un reporte revisable hasta cruzarlos con su fuente/versionado; no se deben vincular por proximidad.

## 3. Contrato y estados del flujo

`POST /api/v1/territory` es la ruta principal. Su orquestación es:

```text
consulta
  → actividad por catálogo/código/alias
  → elección/confirmación si hay ambigüedad o match implícito
  → dirección explícita o patrón calle+altura
  → geocodificación USIG + caché
  → SMP local / contención PostGIS inequívoca
  → barrios/comunas + mixturas + distritos + contexto de uso
  → reglas actividad–mixtura + condiciones medibles
  → mapeo Anexo II + procedimientos realmente cargados
  → respuesta común + fuentes/versiones + advertencias
```

Estados de proceso:

- `needs_activity`: el texto no se resuelve a una actividad del catálogo.
- `needs_activity_confirmation`: hay candidatos y el cliente debe confirmar por código/selección.
- `needs_address`: la actividad quedó confirmada pero falta dirección.
- `partial`: una parte se resolvió, pero faltan datos, regla/mapeo/geometry/procedimientos o una condición relevante.
- `resolved`: solo cuando se satisface el conjunto de requisitos de completitud del servicio. No implica certificación legal.

La compatibilidad es un subresultado independiente: `compatible`, `conditional`, `council_review`, `not_compatible` o `insufficient_data`. Si faltan reglas no debe aparecer una denegación ni permiso inventados.

## 4. Riesgos que el diseño debe bloquear

1. **Variantes de esquema.** El repositorio inspecciona `information_schema`; se mantienen alternativas conocidas, no SQL con columnas supuestas. Cuando una tabla obligatoria carece de la clave esperada se falla de forma controlada.
2. **Migraciones destructivas.** `20261008100000_schema_mvp_final.sql` contiene `DROP TABLE ... CASCADE`. El árbol `supabase/migrations` es el único historial canónico; no volver a ejecutar el archivo sobre la BD cargada. `scripts/migrate.py` solo lista/alerta; no aplica DDL.
3. **Identidad parcelaria incierta.** El SMP canónico conserva sufijos; no se usa `ST_Distance` para elegir una parcela. Cero/múltiples polígonos que contengan el punto se reportan sin coincidencia inequívoca.
4. **Datos de referencia incompletos.** Mixtura vacía, regla ausente, mapeo Anexo II no encontrado o procedimientos vacíos se exponen como datos faltantes, no se convierten a “permitido”.
5. **Alias de actividad.** Se admiten equivalencias explícitas catalogadas, no aproximación difusa. Empates requieren selección humana.
6. **Reglas con valores crudos.** `raw_value` y la condición interpretada deben preservarse para poder auditar cada resultado. Cualquier código no interpretado debe quedar condicional o pendiente, no asumirse compatible.
7. **Fuentes.** Cada dato debe conservar `source_version_id`; la respuesta debe describir versión/URL/checksum cuando existe. No etiquetar una API de geocodificación como proveedora de geometría si esa capacidad no fue comprobada.
8. **Transacciones/ingesta.** Staging, restricciones, `COPY`, `ON CONFLICT` e idempotencia se usan en cargas masivas. No ejecutar una carga completa sin `--dry-run`, muestra y conciliación de claves faltantes.

## 5. Orden productivo recomendado

### Paso 0 — congelar el esquema operativo (bloqueante)

Ejecutar `python scripts/migrate.py`, revisar manualmente `supabase migration list --linked` y ejecutar `python scripts/check_db.py`. Registrar el esquema real de `parcels`, `parcel_geometries`, `urban_parcel_rules`, `geocoding_cache`, `activity_use_rules` y `activity_tramite_mappings`. No correr scripts que apliquen el baseline.

**Aceptación:** no hay tabla/columna base faltante para el flujo; variantes compactas/legacy quedan documentadas y todas las advertencias opcionales se entienden.

### Paso 1 — congelar contratos y pruebas

Mantener el endpoint principal único y los adaptadores heredados. Probar entradas completas, actividad ambigua/no encontrada, dirección ausente, geocoder sin SMP, SMP inexistente, geometry ausente/ambigua, mixtura vacía, regla faltante, distrito especial, mapeo condicional/no encontrado y fallo de proveedor.

**Aceptación:** toda salida tiene un estado claro, `request_id`, `warnings` estables, procedencia cuando disponible y nunca presenta ausencia de datos como compatibilidad.

### Paso 2 — conciliar parcela/SMP y geometrías

Generar un reporte con los SMP que no encontraron `parcels`, decidir si corresponden a versiones distintas, parcelas caducas o errores de normalización. No insertar automáticamente los 233 SMP del reporte sin evidencia fuente. Validar la columna/tabla de caché geométrica y sus índices (GIST + clave parcel_id/SMP). Verificar la geometría real del proveedor antes de darla por parte de USIG.

**Aceptación:** tasa de coincidencia medida; registros residuales explicados; cada geometría enlaza a una parcela por clave verificable.

### Paso 3 — validar el motor actividad × mixtura

Contrastar `activity_use_rules` y sus `raw_value` con el Cuadro 3.3: `SI`, `NO/NPC`, `C`, condiciones numéricas, `SA`, restricciones de frente y excepciones. La evaluación debe iterar todas las mixturas presentes, exponer cada regla y evitar falsos estados verdes cuando falte un parámetro de condición o haya distrito especial.

**Aceptación:** tabla de casos patrón aprobados por el responsable funcional, incluidos datos faltantes y alternativas de mixtura. La elección de una mixtura favorable debe seguir explícitamente la referencia `mapa-usos-caba`, quedar auditada y no ocultar el resto de evaluaciones.

### Paso 4 — cerrar Anexo II y tablas procedimentales

Revisar los 30 códigos sin mapeo automático contra el Anexo II y resolver, con evidencia, si están fuera de su alcance o requieren transcripción/jerarquía. Los 2 casos condicionales deben seguir como opciones hasta que una condición normativa determine el tipo. Después, poblar `procedures`, `activity_procedures`, reglas, requisitos, documentos y pasos desde las fuentes oficiales disponibles.

**Aceptación:** toda fila tiene código de actividad, fuente/página, estado y método; los casos sin resolución explícita nunca tienen tipo por defecto. Las rutas de trámite separan la clasificación de Anexo II del procedimiento detallado.

### Paso 5 — mapa, contexto y frontend

Consumir `/api/v1/map/parcel/{smp}` para GeoJSON; `/api/v1/context/parcel/{smp}` para atributos; `/api/v1/activities/{activity_id}/procedures` para clasificación/detalle y `POST /api/v1/territory` para el proceso inicial. Front debe representar `partial`, `conditional`, `not_compatible` e `insufficient_data` de forma distinta y mostrar fuente/fecha/advertencia.

**Aceptación:** los datos del mapa y del panel de contexto provienen de la misma identidad de parcela y el frontend no requiere acceso directo a PostgreSQL/Supabase.

### Paso 6 — pruebas de integración real y release

Una vez instaladas las dependencias, correr `ruff`, `compileall`, `pytest`, `scripts/check_db.py`, smoke tests HTTP, y probar contra un esquema de pruebas con PostGIS. El paquete actual no demuestra una lectura/escritura real contra el proyecto remoto; esto requiere la URL y permisos del entorno del equipo.

**Aceptación v0.3.0:** flujo determinista reproducible; sin SQL inesperado para esquemas soportados; estados parciales justificados; sin escritura automática de geometría en ingesta parcelaria; sin migraciones destructivas ejecutadas; documentación y colección Postman alineadas a OpenAPI.

## 6. Qué no incluir en este cierre

- No agregar RAG ni LLM al endpoint determinista territorial.
- No intentar resolver automáticamente los 30 códigos pendientes o alias ambiguos por similitud semántica.
- No rellenar polígonos a partir de puntos de geocodificación.
- No convertir los detalles procedimentales vacíos en un objeto ficticio.
- No reestructurar el motor normativo completo hasta validar los casos patrón de este vertical slice.

## 7. Referencias externas a verificar en el adaptador de datos

El portal oficial de USIG documenta funciones de geocodificación y servicios relacionados; sus endpoints de geocodificación no deben asumirse como fuente de polígonos de parcela sin una prueba específica. El catálogo de datos abiertos de CABA ofrece por separado una API de geometría catastral que puede evaluarse si no existe un endpoint de polígono disponible en USIG. La fuente de trámites es la Resolución 96/AGC/25 y su Anexo II: el tipo se debe citar por código y estado de mapeo, no inferirlo del nombre.

## 8. Verificación local de esta entrega

La versión empaquetada se verificó el 13/10/2026 con estos resultados locales:

- `python -m pytest -q`: **77 passed**.
- `python -m compileall -q app ingestion scripts tests`: correcto.
- Los 4 archivos JSON del contrato son válidos.
- `python scripts/migrate.py`: inventario correcto de 9 migraciones; detecta y advierte el baseline destructivo sin ejecutarlo.
- Revisión de duplicados por SHA-256: no hay dos archivos con contenido idéntico en el árbol fuente.
- El ZIP se probó con `ZipFile.testzip()` y excluye bytecode/cachés.

**Límite de validación:** no se abrió una conexión a Supabase ni se ejecutaron escrituras reales. El entorno de construcción carece de `psycopg` y `pgvector`, y no dispone de las credenciales de la base del equipo. Por esto, el paquete es un candidato local verificado, no una certificación de compatibilidad con el esquema remoto. Antes del despliegue, seguir el Paso 0 y el Paso 6 de este roadmap.
