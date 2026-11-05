-- Diagnóstico de solo lectura para el flujo inicial del SGI.
-- Ejecutar en SQL Editor de Supabase. No modifica datos.
-- Si un bloque menciona una tabla que no existe, reportar ese hecho por separado;
-- las tablas opcionales no deben impedir el resto de consultas.

-- 1) Inventario de volumen de las tablas usadas por el flujo.
SELECT 'sources' AS tabla, COUNT(*) AS filas FROM public.sources
UNION ALL SELECT 'source_versions', COUNT(*) FROM public.source_versions
UNION ALL SELECT 'source_resources', COUNT(*) FROM public.source_resources
UNION ALL SELECT 'parcels', COUNT(*) FROM public.parcels
UNION ALL SELECT 'parcel_geometries', COUNT(*) FROM public.parcel_geometries
UNION ALL SELECT 'urban_parcel_rules', COUNT(*) FROM public.urban_parcel_rules
UNION ALL SELECT 'parcel_special_districts', COUNT(*) FROM public.parcel_special_districts
UNION ALL SELECT 'activities', COUNT(*) FROM public.activities
UNION ALL SELECT 'activity_aliases', COUNT(*) FROM public.activity_aliases
UNION ALL SELECT 'activity_use_rules', COUNT(*) FROM public.activity_use_rules
UNION ALL SELECT 'activity_tramite_mappings', COUNT(*) FROM public.activity_tramite_mappings
UNION ALL SELECT 'procedures', COUNT(*) FROM public.procedures
UNION ALL SELECT 'procedure_variants', COUNT(*) FROM public.procedure_variants
UNION ALL SELECT 'activity_procedures', COUNT(*) FROM public.activity_procedures
UNION ALL SELECT 'procedure_rules', COUNT(*) FROM public.procedure_rules
UNION ALL SELECT 'procedure_requirements', COUNT(*) FROM public.procedure_requirements
UNION ALL SELECT 'procedure_documents', COUNT(*) FROM public.procedure_documents
UNION ALL SELECT 'procedure_steps', COUNT(*) FROM public.procedure_steps
UNION ALL SELECT 'geocoding_cache', COUNT(*) FROM public.geocoding_cache
UNION ALL SELECT 'documents', COUNT(*) FROM public.documents
UNION ALL SELECT 'document_chunks', COUNT(*) FROM public.document_chunks
UNION ALL SELECT 'query_runs', COUNT(*) FROM public.query_runs
ORDER BY tabla;

-- 2) Fuentes y versiones que el backend considera vigentes.
SELECT s.code, s.name, sv.id AS source_version_id, sv.version_label, sv.status,
       sv.published_at, sv.effective_from, sv.effective_to
FROM public.sources s
JOIN public.source_versions sv ON sv.source_id = s.id
WHERE sv.status IN ('active', 'ingested')
ORDER BY s.code, sv.effective_from DESC NULLS LAST, sv.id DESC;

-- 3) Formatos de SMP que realmente están guardados (dos/tres dígitos de sección).
SELECT CASE
         WHEN split_part(smp, '-', 1) ~ '^\d{2}$' THEN 'seccion_2_digitos'
         WHEN split_part(smp, '-', 1) ~ '^\d{3}$' THEN 'seccion_3_digitos'
         ELSE 'otro_formato'
       END AS formato,
       COUNT(*) AS parcelas,
       MIN(smp) AS ejemplo_minimo,
       MAX(smp) AS ejemplo_maximo
FROM public.parcels
GROUP BY 1
ORDER BY 1;

-- 4) Integridad parcelaria: parcela sin regla urbanística, geometría o datos administrativos.
SELECT COUNT(*) AS total_parcelas,
       COUNT(*) FILTER (WHERE upr.parcel_id IS NULL) AS sin_regla_urbanistica,
       COUNT(*) FILTER (WHERE pg.parcel_id IS NULL) AS sin_geometria,
       COUNT(*) FILTER (WHERE b.id IS NULL) AS sin_barrio_resoluble,
       COUNT(*) FILTER (WHERE c.id IS NULL) AS sin_comuna_resoluble
FROM public.parcels p
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id = p.id
LEFT JOIN public.parcel_geometries pg ON pg.parcel_id = p.id
LEFT JOIN public.barrios b ON b.id = p.barrio_id
LEFT JOIN public.comunas c ON c.id = COALESCE(p.comuna_id, b.comuna_id);

-- 5) Catálogo de actividades relacionadas con cafetería/café/bar (no selecciona automáticamente).
SELECT a.id, a.code, a.name, a.category, a.mapping_status, a.source_version_id,
       aa.alias, aa.status AS alias_status
FROM public.activities a
LEFT JOIN public.activity_aliases aa ON aa.activity_id = a.id
WHERE lower(a.name) LIKE '%caf%'
   OR lower(COALESCE(a.category, '')) LIKE '%caf%'
   OR lower(COALESCE(aa.alias, '')) LIKE '%caf%'
   OR lower(a.name) LIKE '%bar%'
ORDER BY a.name, aa.alias
LIMIT 100;

-- 6) Reglas de uso/mixtura para actividades encontradas en la consulta anterior.
SELECT a.code AS activity_code, a.name AS activity_name,
       aur.mixtura, aur.raw_value, aur.status, aur.min_surface_m2,
       aur.max_surface_m2, aur.exceeds_max_requires_council,
       aur.special_condition, aur.source_version_id
FROM public.activity_use_rules aur
JOIN public.activities a ON a.id = aur.activity_id
WHERE lower(a.name) LIKE '%caf%'
   OR lower(a.name) LIKE '%bar%'
ORDER BY a.name, aur.mixtura, aur.id
LIMIT 200;

-- 7) Relación actividad -> tipo de trámite (Anexo II), con trazabilidad del origen.
SELECT a.id AS activity_id, a.code, a.name,
       atm.mapping_status, atm.mapping_method, atm.annex_ii_activity_name_verified,
       atm.procedure_type_code, atm.procedure_type_label,
       atm.possible_procedure_type_codes, atm.source_annex_id,
       atm.annex_ii_page, sv.version_label, sv.status AS source_status
FROM public.activities a
LEFT JOIN public.activity_tramite_mappings atm ON atm.activity_id = a.id
LEFT JOIN public.source_versions sv ON sv.id = atm.source_version_id
WHERE lower(a.name) LIKE '%caf%'
   OR lower(a.name) LIKE '%bar%'
ORDER BY a.name, atm.id;

-- 8) Estado de los vínculos y detalle del catálogo de trámites.
SELECT (SELECT COUNT(*) FROM public.activity_procedures) AS activity_procedure_rows,
       (SELECT COUNT(*) FROM public.procedures) AS procedure_rows,
       (SELECT COUNT(*) FROM public.procedure_variants) AS procedure_variant_rows,
       (SELECT COUNT(*) FROM public.procedure_requirements) AS requirement_rows,
       (SELECT COUNT(*) FROM public.procedure_documents) AS document_rows,
       (SELECT COUNT(*) FROM public.procedure_steps) AS step_rows,
       (SELECT COUNT(*) FROM public.procedure_rules) AS procedure_rule_rows;

-- 9) Mapeos activos sin detalle equivalente en procedure_variants.
SELECT atm.id AS mapping_id, a.code AS activity_code, a.name AS activity_name,
       atm.mapping_status, atm.procedure_type_code, atm.possible_procedure_type_codes,
       COUNT(pv.id) AS matching_variants
FROM public.activity_tramite_mappings atm
JOIN public.activities a ON a.id = atm.activity_id
JOIN public.source_versions sv ON sv.id = atm.source_version_id
LEFT JOIN public.procedure_variants pv
  ON pv.code = atm.procedure_type_code
  OR pv.code = ANY(atm.possible_procedure_type_codes)
WHERE sv.status IN ('active', 'ingested')
GROUP BY atm.id, a.code, a.name, atm.mapping_status,
         atm.procedure_type_code, atm.possible_procedure_type_codes
HAVING COUNT(pv.id) = 0
ORDER BY a.name
LIMIT 200;

-- 10) Caché USIG para Corrientes 2500 y parcela enlazada (si la fila existe).
SELECT gc.input_address, gc.normalized_street, gc.height, gc.latitude, gc.longitude,
       gc.smp AS cached_smp, gc.resolved_parcel_id, p.smp AS parcel_smp,
       gc.fetched_at, gc.expires_at, gc.source_version_id
FROM public.geocoding_cache gc
LEFT JOIN public.parcels p
  ON p.id = gc.resolved_parcel_id OR p.smp = gc.smp
WHERE lower(gc.input_address) LIKE '%corrientes%'
  AND (gc.height = 2500 OR lower(gc.input_address) LIKE '%2500%')
ORDER BY gc.fetched_at DESC
LIMIT 20;

-- 11) Distribución de estados del mapeo del Anexo II.
SELECT mapping_status, procedure_type_code, COUNT(*) AS filas
FROM public.activity_tramite_mappings
GROUP BY mapping_status, procedure_type_code
ORDER BY mapping_status, procedure_type_code;

-- 12) Índices relevantes para las consultas del flujo.
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
    'parcels', 'parcel_geometries', 'urban_parcel_rules',
    'activity_use_rules', 'activity_tramite_mappings', 'activity_aliases',
    'geocoding_cache', 'activity_procedures', 'procedure_variants'
  )
ORDER BY tablename, indexname;


-- 13) Columnas reales de auditoría. Permite comparar la base remota con la versión
-- del backend sin asumir que la migración opcional de auditoría estructurada ya se aplicó.
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('query_runs', 'query_evidence')
ORDER BY table_name, ordinal_position;
