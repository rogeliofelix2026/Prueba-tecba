# Diagnóstico de campos y completitud del flujo — v0.3.4

## Conclusión ejecutiva

Los datos compartidos muestran que geocodificación, parcela, barrio/comuna y reglas urbanísticas ya funcionan para `Corrientes 2880` (SMP `013-098-006B`, parcela 127966, barrio Balvanera, Comuna 3, mixtura 4). Las principales brechas son: alias humano inexistente, cruce del código de Anexo II con códigos internos de variantes, fuente de geometría no configurada y tabla RUS vacía.

## 1. Identidad de parcela y consulta SQL

`parcels.id` es PK y `parcels.smp` es UNIQUE. `urban_parcel_rules.parcel_id` tiene UNIQUE/FK a `parcels.id`. El query `FROM parcels, urban_parcel_rules WHERE parcel_id = ...` no expresa relación entre ambas tablas, así que genera producto cartesiano: muchas SMP aparecen junto al mismo `urban_parcel_rules.id`. Siempre usar `JOIN urban_parcel_rules upr ON upr.parcel_id = p.id`. No regenerar IDs ni volver a importar las tablas por esa salida.

## 2. Actividad

El catálogo tiene 325 registros y los alias recibidos no incluían `Cafetería`. La migración agrega el alias `cafeteria` a `1.5 — Alimentación en general y gastronomía`, pero con estado `provisional`. La aplicación puede recuperar sus reglas y mostrar un preview determinista, pero debe requerir confirmación del usuario antes de tratarlo como selección comercial definitiva. Para robustecer el vocabulario, los próximos alias deben salir de un catálogo revisado y no de coincidencias difusas arbitrarias.

## 3. Compatibilidad urbana

La consulta de `Corrientes 2880` reporta la mixtura `[4]` y una regla de Código Urbanístico. La evaluación usa esa regla junto con `activity_use_rules`, no `land_use_observations`. Hay 152 de 318.046 parcelas sin regla urbanística: para esos casos, devolver contexto administrativo si existe, estado parcial y no inferir compatibilidad. La ausencia de superficie del local no se puede reemplazar por el tamaño del lote o `partida_ma`.

## 4. Geometría

USIG GeoCoder 2.2 documenta `/geocoding`, `/reversegeocoding` y `/smp`, donde `/smp` obtiene nomenclatura catastral a partir de calle/altura; no documenta la descarga del polígono del lote. Referencias: https://ws.usig.buenosaires.gob.ar/geocoder/2.2.

El recurso oficial **Parcelas (GeoJSON)** publica geometría de cada parcela y atributos como SMP: https://data.buenosaires.gob.ar/dataset/juqdkmgo-156/resource/8d8ffe66-9eb9-4f12-8f23-e1586a2d888d. Se cachea solo el polígono del SMP solicitado en `parcel_geometries`. Para rendimiento, se recomienda GeoPackage con índice B-tree por `smp`, fuente persistida/montada en cada instancia y versión de `sources.code='parcelas'` claramente asociada al archivo. El backend exige `PARCEL_GEOMETRY_SOURCE_VERSION_ID` cuando se configura una ruta: no deduce esa relación a partir de la versión más reciente.

`include_geometry=false` no necesita serializar el polígono, pero la opción `PARCEL_GEOMETRY_CACHE_ON_RESOLVE=true` permite obtenerlo y cachearlo la primera vez que se resuelve la parcela si una fuente local está configurada. La siguiente consulta reutiliza la geometría de PostGIS. Sin `PARCEL_GEOMETRY_SOURCE_PATH`, no puede poblarse sola; solo se devuelve una advertencia. Esta dependencia externa es intencional, porque no se debe inventar un polígono a partir de coordenadas de punto.

## 5. Trámites y fuentes oficiales

La clasificación de Anexo II y los detalles procedimentales son entidades diferentes. `activity_procedures` puede seguir vacío: para determinar el tipo inicial se utiliza `activity_tramite_mappings`, luego un crosswalk explícito enlaza `DDRR_CP` a `DDRR_CON_PLANO`, `DDRR_SP` a `DDRR_SIN_PLANO`, `DDRR_E` a su variante exprés y `LICENCIA` a `LICENCIA`. Los detalles deben estar relacionados por el `procedure_id` real y llevar versionado.

Fuente AGC para modalidad exprés: https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=1. Enumera como condiciones, entre otras, superficie de hasta 200 m², actividades no excluidas, ubicación no excluida, edificios no catalogados, accesibilidad y ausencia de entrepisos. Si alguna no se cumple, debe evaluarse el trámite general con intervención profesional. La app no concluye que un local sea elegible para exprés cuando todavía se desconoce la superficie o el resto de condiciones.

El servicio https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=2 sirve para consultar el estado de un trámite existente usando número de expediente/solicitud, no para clasificar el trámite nuevo.

La guía general https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica señala que DDRR sin planos se usa hasta 500 m²; declaraciones con/sin planos pueden iniciar actividad tras su presentación, sujetas a revisión técnica final, mientras que una licencia requiere aprobación y una inspección previa antes de empezar. No presentar “inicio inmediato” como habilitación definitiva.

## 6. Uso del suelo observado (RUS)

El dataset `land_use_observations` está vacío. RUS aporta observaciones sobre usos existentes, estado o atributos de edificios, pero no reemplaza el cuadro normativo del Código Urbanístico. Para el análisis de compatibilidad legal del MVP **no es requisito bloqueante**. Mantener la respuesta `land_use=[]` con warning opcional hasta que se cargue el dataset; no llenar observaciones con inferencias.

## 7. Campos que pueden seguir en null

- `query.address_extracted`: null cuando se recibió una dirección explícita.
- `surface_m2`, `street_width_m`, `frontage_m`: null si el usuario no los dio y no existe fuente confiable que informe esos atributos del local. El sistema debe solicitar estos datos cuando la regla/condición elegida los necesite.
- `territory.parcel.geometry`: null cuando no hay geometría cacheada, no se configuró archivo, o `include_geometry=false` evita serializarla. Revisar `geometry_status`, `geometry_cached` y `geometry_source_version_id`.
- `territory.useful_data`: omite propiedades vacías que USIG devuelve como `""`; esas propiedades no representan un dato recuperado.
- `territory.land_use`: vacío por falta de datos RUS cargados; opcional.
- `activity_tramite_mappings.annex_ii_activity_name_verified`: algunos registros pueden no tener la denominación oficial verificada, sin borrar el tipo mapeado. Debe mantenerse como deuda de calidad trazable.
- `sources.checksum_sha256`: puede ser null si el proceso de ingesta no calculó checksum de la fuente original.
- `compatibility` y `procedure_type_mapping`: antes de la migración podían quedar null por `ACTIVITY_NOT_FOUND_IN_CATALOG`; después, deben resolverse para alias 1.5 si el mapeo está vigente y el repositorio operativo.

## 8. Aplicación

1. Aplicar una sola vez `supabase/migrations/20261013140000_mvp_flow_completion.sql` (idempotente).
2. Descargar Parcelas, convertir a GeoPackage e indexar SMP.
3. Confirmar el ID correcto en `source_versions` para `sources.code='parcelas'` y configurarlo en `PARCEL_GEOMETRY_SOURCE_VERSION_ID`.
4. Configurar la ruta de la fuente geométrica en `.env`/entorno de despliegue y reiniciar el backend.
5. Ejecutar el smoke test del plan y `docs/sql/diagnostico_v034_flujo_completo.sql`.

No se ha ejecutado una consulta directa contra tu Supabase; la validación contra datos remotos sigue pendiente hasta que el equipo aplique la migración y pruebe con sus credenciales.
