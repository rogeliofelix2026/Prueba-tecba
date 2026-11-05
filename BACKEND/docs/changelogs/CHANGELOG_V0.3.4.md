# Cambios SGI Backend v0.3.4

## Integridad de datos y resolución

- Alias provisional `Cafetería` → actividad `1.5`, sin convertirlo en asignación normativa definitiva.
- El flujo sigue resolviendo dirección aunque actividad no se reconozca.
- Crosswalk explícito de códigos del Anexo II hacia variantes reales de la base; ya no depende de que `activity_procedures` esté poblada.
- Campo SQL del candidato de trámite no usa alias duplicados dentro del CTE, y conserva correctamente cada candidato cuando el mapeo es condicional.
- Las advertencias de RUS faltante distinguen tabla inexistente, dataset vacío y ausencia de registros para una parcela; RUS no bloquea la compatibilidad normativa.

## Geometría

- Servicio `ParcelGeometryProvider` obtiene solo el polígono del SMP consultado desde una fuente catastral local/montada.
- Búsqueda por igualdad de SMP preparada para índice B-tree/GeoPackage; variantes de sección y capitalización contempladas.
- La geometría se escribe en `parcel_geometries` con versión de fuente de `sources.code='parcelas'`, checksum y timestamp.
- `geometry_status` permite distinguir caché existente, falta de configuración, fallo de fuente y caché fallida.
- El punto geocodificado de USIG nunca se transforma en polígono sintético.

## Trámites y fuentes oficiales

- Migración idempotente: `supabase/migrations/20261013140000_mvp_flow_completion.sql`.
- Incluye detalles iniciales trazables de elegibilidad y pasos de la modalidad exprés según la página oficial AGC; no selecciona esta modalidad de forma automática solo porque el rubro sea gastronomía.
- Se documentan campos que legítimamente quedan en `null` cuando requieren información del local que no fue provista.

## Verificación

- Añadidas pruebas de regresión para el alias provisional, crosswalk de trámites y búsquedas indexables de geometría.
- Se agregó SQL de diagnóstico de solo lectura: `docs/sql/diagnostico_v034_flujo_completo.sql`.
- Pendiente prueba contra una instancia real de Supabase y una fuente geométrica oficial configurada.
