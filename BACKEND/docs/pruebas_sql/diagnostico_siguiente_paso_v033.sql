-- Diagnóstico de solo lectura para el flujo /api/v1/territory.
-- Ejecutar después de aplicar 20261013110000_repair_activity_lookup_and_optional_context.sql.
-- No muestra secretos ni modifica registros.

-- 1) Actividad candidata y alias usados por el ejemplo Cafetería.
SELECT a.id, a.code, a.name, a.mapping_status, a.source_version_id AS activity_source_version_id,
       aa.alias, aa.normalized_alias, aa.status AS alias_status,
       aa.source_version_id AS alias_source_version_id, alias_sv.status AS alias_source_status
FROM public.activities a
LEFT JOIN public.activity_aliases aa ON aa.activity_id = a.id
LEFT JOIN public.source_versions alias_sv ON alias_sv.id = aa.source_version_id
WHERE a.code = '1.5' OR aa.normalized_alias IN ('cafeteria', 'cafe')
ORDER BY a.code, aa.normalized_alias;

-- 2) Mapeo de Anexo II del código 1.5 y posibles variantes procedimentales coincidentes.
SELECT a.code AS activity_code, a.name AS activity_name,
       atm.mapping_status, atm.procedure_type_code, atm.possible_procedure_type_codes,
       atm.source_version_id AS mapping_source_version_id,
       pv.code AS variant_code, pv.name AS variant_name, pv.active AS variant_active,
       p.code AS procedure_code, p.name AS procedure_name,
       psv.status AS procedure_source_status, vsv.status AS variant_source_status,
       pv.source_version_id AS variant_source_version_id
FROM public.activities a
LEFT JOIN public.activity_tramite_mappings atm ON atm.activity_id = a.id
LEFT JOIN public.procedure_variants pv
  ON pv.code = atm.procedure_type_code
  OR pv.code = ANY(COALESCE(atm.possible_procedure_type_codes, ARRAY[]::text[]))
LEFT JOIN public.procedures p ON p.id = pv.procedure_id
LEFT JOIN public.source_versions psv ON psv.id = p.source_version_id
LEFT JOIN public.source_versions vsv ON vsv.id = pv.source_version_id
WHERE a.code = '1.5'
ORDER BY atm.id, pv.code;

-- 3) Inventario de variantes reales y procedencia (útil si el mapeo no encuentra variantes).
SELECT p.code AS procedure_code, p.name AS procedure_name,
       pv.code AS variant_code, pv.name AS variant_name,
       pv.active, pv.conditions, pv.source_version_id,
       sv.version_label, sv.status AS source_status, s.code AS source_code
FROM public.procedure_variants pv
JOIN public.procedures p ON p.id = pv.procedure_id
JOIN public.source_versions sv ON sv.id = pv.source_version_id
JOIN public.sources s ON s.id = sv.source_id
ORDER BY p.code, pv.code;

-- 4) Versiones vigentes/ingestadas de las fuentes fundamentales.
SELECT s.code, s.name, sv.id AS source_version_id, sv.version_label,
       sv.status, sv.published_at, sv.effective_from, sv.effective_to
FROM public.sources s
JOIN public.source_versions sv ON sv.source_id = s.id
WHERE s.code IN (
    'usig', 'parcelas', 'codigo_urbanistico', 'relevamiento_usos_suelo',
    'resolucion_96_agc_25_anexo_ii', 'gcba_habilitacion_actividad', 'gcba_habilitacion_expres'
)
ORDER BY s.code, (sv.status = 'active') DESC, sv.id DESC;

-- 5) Últimas solicitudes geocodificadas y vínculo por SMP con datos territoriales.
SELECT gc.id AS cache_id, gc.input_address, gc.normalized_street, gc.street_code, gc.height,
       gc.latitude, gc.longitude, gc.smp, gc.resolved_parcel_id,
       p.id AS parcel_id, p.smp AS parcel_smp,
       b.name AS barrio, c.name AS comuna,
       upr.mixturas, upr.source_version_id AS urban_rule_source_version_id,
       gc.source_version_id AS geocoding_source_version_id,
       gc.fetched_at, gc.expires_at, gc.response_json->'warnings' AS geocoding_warnings
FROM public.geocoding_cache gc
LEFT JOIN public.parcels p ON p.id = gc.resolved_parcel_id OR p.smp = gc.smp
LEFT JOIN public.barrios b ON b.id = p.barrio_id
LEFT JOIN public.comunas c ON c.id = p.comuna_id
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id = p.id
WHERE gc.input_address ILIKE '%corrientes%' OR gc.normalized_street ILIKE '%corrientes%'
ORDER BY gc.fetched_at DESC NULLS LAST
LIMIT 20;

-- 6) Cobertura real de geocoding, parcela y regla urbanística.
SELECT COUNT(*) AS cache_rows,
       COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) AS rows_with_coords,
       COUNT(*) FILTER (WHERE smp IS NOT NULL) AS rows_with_smp,
       COUNT(*) FILTER (WHERE p.id IS NOT NULL) AS rows_linked_to_parcel,
       COUNT(*) FILTER (WHERE b.id IS NOT NULL) AS rows_with_barrio,
       COUNT(*) FILTER (WHERE c.id IS NOT NULL) AS rows_with_comuna,
       COUNT(*) FILTER (WHERE upr.parcel_id IS NOT NULL) AS rows_with_urban_rule
FROM public.geocoding_cache gc
LEFT JOIN public.parcels p ON p.id = gc.resolved_parcel_id OR p.smp = gc.smp
LEFT JOIN public.barrios b ON b.id = p.barrio_id
LEFT JOIN public.comunas c ON c.id = p.comuna_id
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id = p.id;

-- 7) Estado de RUS: la tabla creada no implica que los datos estén ingeridos.
SELECT COUNT(*) AS rus_rows,
       COUNT(*) FILTER (WHERE parcel_id IS NOT NULL) AS rus_rows_linked_to_parcel,
       COUNT(DISTINCT parcel_id) FILTER (WHERE parcel_id IS NOT NULL) AS parcels_with_rus,
       MIN(anio) AS min_year, MAX(anio) AS max_year
FROM public.land_use_observations;

-- 8) Geometry cache: debería crecer por parcela solicitada, no por una carga completa.
SELECT COUNT(*) AS cached_geometries,
       COUNT(DISTINCT parcel_id) AS distinct_parcels,
       COUNT(*) FILTER (WHERE ST_IsValid(geom) AND NOT ST_IsEmpty(geom)) AS valid_nonempty_geometries,
       COUNT(*) FILTER (WHERE ST_SRID(geom) = 4326) AS geometries_epsg_4326
FROM public.parcel_geometries;

-- 9) Tabla de alias y variantes: columnas actuales vs modelo esperado.
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('activity_aliases', 'activity_tramite_mappings', 'procedure_variants', 'land_use_observations', 'parcel_geometries')
ORDER BY table_name, ordinal_position;

-- 10) Cobertura de atributos estructurados por parcela.
SELECT COUNT(*) AS total_parcels,
       COUNT(*) FILTER (WHERE upr.parcel_id IS NULL) AS parcels_without_urban_rule,
       COUNT(*) FILTER (WHERE b.id IS NULL) AS parcels_without_barrio_join,
       COUNT(*) FILTER (WHERE c.id IS NULL) AS parcels_without_comuna_join
FROM public.parcels p
LEFT JOIN public.barrios b ON b.id = p.barrio_id
LEFT JOIN public.comunas c ON c.id = p.comuna_id
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id = p.id;
