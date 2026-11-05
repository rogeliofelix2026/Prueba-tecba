-- Diagnóstico READ-ONLY SGI v0.3.4. Ejecutar en Supabase SQL Editor.
-- No modifica filas. Cada sección puede ejecutarse de forma independiente.

-- 1. Integridad real para la parcela de ejemplo. No usar FROM parcels, urban_parcel_rules sin JOIN.
SELECT p.id AS parcel_id, p.smp, p.partida_ma, b.name AS barrio, c.name AS comuna,
       upr.id AS urban_rule_id, upr.mixturas, upr.catalogado, upr.rh,
       upr.ensanche, upr.apertura, upr.lep, upr.ci_digital, upr.anac,
       upr.source_version_id AS urban_rule_source_version_id
FROM public.parcels p
LEFT JOIN public.barrios b ON b.id = p.barrio_id
LEFT JOIN public.comunas c ON c.id = p.comuna_id
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id = p.id
WHERE p.smp = '013-098-006B';

-- 2. Duplicados de reglas por parcela: debería devolver 0 filas por el índice unique.
SELECT parcel_id, COUNT(*) AS rows_per_parcel
FROM public.urban_parcel_rules GROUP BY parcel_id HAVING COUNT(*) > 1 LIMIT 100;

-- 3. Actividad, alias y tipo de trámite para cafetería / actividad 1.5.
SELECT a.id, a.code, a.name, a.mapping_status, a.source_version_id AS activity_source_version_id,
       aa.alias, aa.normalized_alias, aa.status AS alias_status, aa.source_version_id AS alias_source_version_id,
       sv.status AS alias_source_status, atm.mapping_status AS tramite_mapping_status,
       atm.procedure_type_code, atm.procedure_type_label, atm.source_version_id AS mapping_source_version_id
FROM public.activities a
LEFT JOIN public.activity_aliases aa ON aa.activity_id = a.id AND aa.normalized_alias = 'cafeteria'
LEFT JOIN public.source_versions sv ON sv.id = aa.source_version_id
LEFT JOIN LATERAL (
  SELECT m.* FROM public.activity_tramite_mappings m
  JOIN public.source_versions msv ON msv.id = m.source_version_id
  WHERE m.activity_id = a.id AND msv.status IN ('active','ingested')
  ORDER BY (msv.status='active') DESC, COALESCE(msv.effective_from, msv.published_at) DESC NULLS LAST, msv.id DESC
  LIMIT 1
) atm ON true
WHERE a.code = '1.5';

-- 4. Crosswalk Anexo II -> variantes existentes. Se espera CP -> DDRR_CON_PLANO,
-- SP -> DDRR_SIN_PLANO, E -> DDRR_E y LICENCIA -> LICENCIA.
WITH crosswalk(procedure_type_code, variant_code) AS (
  VALUES ('DDRR_CP','DDRR_CON_PLANO'), ('DDRR_SP','DDRR_SIN_PLANO'),
         ('DDRR_E','DDRR_E'), ('LICENCIA','LICENCIA')
)
SELECT x.procedure_type_code, x.variant_code, pv.id AS variant_id, pv.name AS variant_name,
       pv.active, p.code AS procedure_code, p.name AS procedure_name,
       sv.status AS variant_source_status, sv.id AS variant_source_version_id
FROM crosswalk x
LEFT JOIN public.procedure_variants pv ON pv.code = x.variant_code
LEFT JOIN public.procedures p ON p.id = pv.procedure_id
LEFT JOIN public.source_versions sv ON sv.id = pv.source_version_id
ORDER BY x.procedure_type_code, pv.id;

-- 5. Procedimiento seleccionado por la actividad 1.5 y sus detalles asociados.
SELECT p.code, p.name, pv.code AS variant_code, pv.name AS variant_name,
       (SELECT COUNT(*) FROM public.procedure_requirements pr WHERE pr.procedure_id=p.id) AS requirements,
       (SELECT COUNT(*) FROM public.procedure_documents pd WHERE pd.procedure_id=p.id) AS documents,
       (SELECT COUNT(*) FROM public.procedure_steps ps WHERE ps.procedure_id=p.id) AS steps
FROM public.procedures p
LEFT JOIN public.procedure_variants pv ON pv.procedure_id = p.id AND COALESCE(pv.active, true)
ORDER BY p.code, pv.code;

-- 6. Geometrías cacheadas: la procedencia debe ser sources.code='parcelas', no 'usig',
-- cuando se carga desde el recurso catastral oficial.
SELECT COUNT(*) AS cached_geometries,
       COUNT(DISTINCT pg.parcel_id) AS distinct_parcels,
       COUNT(*) FILTER (WHERE NOT ST_IsEmpty(pg.geom) AND ST_IsValid(pg.geom)) AS valid_geometries,
       COUNT(*) FILTER (WHERE ST_SRID(pg.geom)=4326) AS srid_4326,
       COUNT(*) FILTER (WHERE s.code='parcelas') AS source_parcelas,
       COUNT(*) FILTER (WHERE s.code<>'parcelas' OR s.code IS NULL) AS unexpected_source
FROM public.parcel_geometries pg
LEFT JOIN public.source_versions sv ON sv.id=pg.source_version_id
LEFT JOIN public.sources s ON s.id=sv.source_id;

-- 7. Geometría y versión para la parcela de ejemplo.
SELECT p.id, p.smp, pg.source_version_id, s.code AS geometry_source_code,
       sv.version_label, sv.status, pg.loaded_at, pg.checksum_sha256,
       ST_SRID(pg.geom) AS srid, GeometryType(pg.geom) AS geometry_type,
       ST_IsValid(pg.geom) AS is_valid, ST_IsEmpty(pg.geom) AS is_empty
FROM public.parcels p
LEFT JOIN public.parcel_geometries pg ON pg.parcel_id = p.id
LEFT JOIN public.source_versions sv ON sv.id = pg.source_version_id
LEFT JOIN public.sources s ON s.id = sv.source_id
WHERE p.smp = '013-098-006B';

-- 8. RUS es opcional: estado de carga y porcentaje enlazado a parcelas.
SELECT COUNT(*) AS rus_rows,
       COUNT(*) FILTER (WHERE parcel_id IS NOT NULL) AS linked_rows,
       COUNT(DISTINCT parcel_id) FILTER (WHERE parcel_id IS NOT NULL) AS parcels_with_rus,
       MIN(anio) AS min_year, MAX(anio) AS max_year
FROM public.land_use_observations;

-- 9. Parcelas sin regla territorial (los 152 que pueden quedar sin compatibilidad).
SELECT p.id, p.smp, p.barrio_id, p.comuna_id
FROM public.parcels p
LEFT JOIN public.urban_parcel_rules upr ON upr.parcel_id=p.id
WHERE upr.parcel_id IS NULL
ORDER BY p.smp LIMIT 200;

-- 10. Versiones de fuentes asociadas a los datos estructurados; verificar estado y fechas.
SELECT s.code, s.name, sv.id AS source_version_id, sv.version_label, sv.status,
       sv.published_at, sv.effective_from, sv.effective_to
FROM public.sources s JOIN public.source_versions sv ON sv.source_id=s.id
WHERE s.code IN ('parcelas','codigo_urbanistico','relevamiento_usos_suelo',
                 'resolucion_96_agc_25_anexo_ii','gcba_habilitacion_actividad','gcba_habilitacion_expres')
ORDER BY s.code, sv.id;
