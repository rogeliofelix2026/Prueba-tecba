# SGI Backend v0.3.3 — resolución territorial y caché geográfica

- La actividad y la dirección se resuelven de forma independiente: una actividad desconocida o ambigua ya no impide geocodificar ni recuperar parcela, barrio/comuna y reglas urbanísticas.
- Un alias provisional único produce una vista previa de compatibilidad claramente marcada y conserva `needs_activity_confirmation`; no se presenta como resultado jurídico definitivo.
- Se incorpora una migración aditiva que repone el alias provisional `cafetería` para la actividad `1.5`, agrega la columna opcional `procedure_variants.active` y recrea `land_use_observations` si falta.
- La carga de detalles procedimentales desde `activity_tramite_mappings` ahora soporta esquemas donde `procedure_variants.active` todavía no existía; la tabla `activity_procedures` puede permanecer vacía o faltar sin bloquear la clasificación del Anexo II.
- El ingestor RUS normaliza el SMP al relacionar observaciones con parcelas, reduciendo pérdidas por secciones que llegan en dos o tres dígitos.
- El ingreso de geometrías completo requiere `--all` explícito. Se agrega `ingestion/cache_parcel_geometry.py` para cachear un solo polígono por SMP en `parcel_geometries`.
- Se conserva la migración histórica sin reescribirla: el pipeline recomendado ingiere atributos sin geometría inline y cachea polígonos solicitados por separado.
- Se evita cachear por accidente polígonos de entidades no parcelarias presentes en respuestas complementarias de USIG.
- Se añaden pruebas del flujo con actividad sin resolver, alias provisional, fallback de trámites sin tabla asociativa y extracción segura de GeoJSON poligonal.

## Límites verificados

Las pruebas unitarias se ejecutan con stubs temporales de importación en el entorno sin drivers PostgreSQL/pgvector; no reemplazan la prueba conectada a Supabase. El GeoCoder de USIG documenta resolución de coordenadas, reverse geocoding y SMP, no la entrega del polígono de parcela. `parcel_geometries` permanece vacío hasta que un adaptador aporte geometría catastral real. La tabla de usos observados puede crearse con la migración, pero requiere cargar el CSV RUS real para producir observaciones.
