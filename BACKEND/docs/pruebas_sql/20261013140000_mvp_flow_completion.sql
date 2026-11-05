-- v0.3.4: completar resolución básica de actividad y mapeo de variantes.
-- Es idempotente. No cambia parcelas ni reglas urbanísticas existentes.
BEGIN;

-- "Cafetería" no figura como rubro canónico del catálogo recibido. Se trata como
-- alias provisional de 1.5 para permitir vista previa, nunca como confirmación legal.
INSERT INTO public.activity_aliases
    (activity_id, alias, normalized_alias, status, source_version_id)
SELECT a.id, 'Cafetería', 'cafeteria', 'provisional', NULL
FROM public.activities a
WHERE a.code = '1.5'
  AND NOT EXISTS (
      SELECT 1 FROM public.activity_aliases aa
      WHERE aa.activity_id = a.id AND aa.normalized_alias = 'cafeteria'
  );

-- Variante expresa independiente: la fuente oficial de Habilitación Exprés se
-- mantiene separada de DDRR sin/con plano y de Licencia.
INSERT INTO public.procedures (code, name, description, source_version_id)
SELECT
    'habilitacion_actividad_economica_expres',
    'Habilitación de actividad económica exprés',
    'Modalidad exprés sujeta a las condiciones de elegibilidad publicadas por AGC/GCBA. La clasificación automática no reemplaza la confirmación oficial.',
    sv.id
FROM public.source_versions sv
JOIN public.sources s ON s.id = sv.source_id
WHERE s.code = 'gcba_habilitacion_expres'
  AND sv.status IN ('active', 'ingested')
ORDER BY (sv.status = 'active') DESC,
         COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
         sv.id DESC
LIMIT 1
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.procedure_variants
    (procedure_id, code, name, description, conditions,
     immediate_start_allowed, prior_inspection_required, validity_years,
     source_version_id, active)
SELECT
    p.id,
    'DDRR_E',
    'Declaración responsable exprés',
    'Solo aplicable cuando se cumplen todos los requisitos oficiales de la modalidad exprés. Confirmar los requisitos vigentes con AGC/GCBA.',
    jsonb_build_object(
        'surface_max_m2', 200,
        'excluded_products', jsonb_build_array('explosivos', 'inflamables', 'medicamentos sin envasar'),
        'excluded_locations', jsonb_build_array('galerías', 'centros comerciales', 'paseos de compras', 'mercados', 'patios gastronómicos', 'estaciones de subte o tren', 'aeropuertos', 'complejos comerciales'),
        'special_or_protected_area_not_allowed', true,
        'catalogued_building_not_allowed', true,
        'accessibility_compliance_required', true,
        'mezzanines_not_allowed', true,
        'activity_specific_regulation_may_exclude', true,
        'source_url', 'https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=1'
    ),
    true,
    false,
    NULL,
    sv.id,
    true
FROM public.procedures p
JOIN public.source_versions psv ON psv.id = p.source_version_id
JOIN public.sources ps ON ps.id = psv.source_id
JOIN public.source_versions sv ON sv.source_id = ps.id AND sv.id = p.source_version_id
WHERE p.code = 'habilitacion_actividad_economica_expres'
  AND ps.code = 'gcba_habilitacion_expres'
  AND NOT EXISTS (
      SELECT 1 FROM public.procedure_variants pv
      WHERE pv.procedure_id = p.id AND pv.code = 'DDRR_E'
  );

-- Requisito condicionado y pasos mínimos trazables. Las condiciones de elegibilidad
-- se presentan como información oficial a verificar, no como un dictamen automático.
INSERT INTO public.procedure_requirements
    (procedure_id, requirement_code, title, description, conditional, conditions, source_version_id)
SELECT p.id, 'ELIGIBILIDAD_DDRR_E', 'Cumplir las condiciones de Habilitación Exprés',
       'Verificar superficie (hasta 200 m²) y todas las exclusiones de ubicación, actividad, edificio, accesibilidad y entrepisos indicadas por AGC/GCBA. Si alguna condición no se cumple, evaluar la modalidad general correspondiente.',
       false,
       jsonb_build_object('must_check_all_conditions', true, 'source_url', 'https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=1'),
       sv.id
FROM public.procedures p
JOIN public.source_versions sv ON sv.id = p.source_version_id
JOIN public.sources s ON s.id = sv.source_id
WHERE p.code = 'habilitacion_actividad_economica_expres'
  AND s.code = 'gcba_habilitacion_expres'
  AND NOT EXISTS (
      SELECT 1 FROM public.procedure_requirements pr
      WHERE pr.procedure_id = p.id AND pr.requirement_code = 'ELIGIBILIDAD_DDRR_E'
  );

INSERT INTO public.procedure_steps (procedure_id, step_order, title, description, source_version_id)
SELECT p.id, x.step_order, x.title, x.description, sv.id
FROM public.procedures p
JOIN public.source_versions sv ON sv.id = p.source_version_id
JOIN public.sources s ON s.id = sv.source_id
CROSS JOIN (VALUES
  (1, 'Verificar elegibilidad de la modalidad exprés', 'Comprobar la superficie máxima y todas las exclusiones oficiales antes de sugerir esta vía.'),
  (2, 'Ingresar a la plataforma oficial', 'Iniciar la solicitud en TAD/AGC con el nivel de identidad miBA exigido por la plataforma vigente.'),
  (3, 'Completar la solicitud y atender la evaluación oficial', 'Declarar titular, unidad de uso y actividad; completar los datos y documentos que la plataforma solicite. La clasificación orientativa del SGI no otorga la habilitación.')
) AS x(step_order, title, description)
WHERE p.code = 'habilitacion_actividad_economica_expres'
  AND s.code = 'gcba_habilitacion_expres'
  AND NOT EXISTS (
      SELECT 1 FROM public.procedure_steps ps
      WHERE ps.procedure_id = p.id AND ps.step_order = x.step_order
  );

-- Documento adicional marcado como condicional, porque la fuente oficial especifica
-- que puede corresponder según el caso y la actividad.
INSERT INTO public.procedure_documents
    (procedure_id, document_code, title, description, conditional, conditions, source_version_id)
SELECT p.id, 'CAA', 'Certificado de Aptitud Ambiental (cuando corresponda)',
       'La documentación oficial lo enumera entre los documentos complementarios; verificar su exigibilidad para el caso concreto y la modalidad elegida.',
       true,
       jsonb_build_object('verify_applicability', true, 'source_url', 'https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica'),
       doc_sv.id
FROM public.procedures p
JOIN public.source_versions proc_sv ON proc_sv.id = p.source_version_id
JOIN public.sources proc_s ON proc_s.id = proc_sv.source_id
JOIN public.sources doc_s ON doc_s.code = 'gcba_autorizacion_actividades_pdf'
JOIN LATERAL (
    SELECT sv.id FROM public.source_versions sv
    WHERE sv.source_id = doc_s.id AND sv.status IN ('active', 'ingested')
    ORDER BY (sv.status = 'active') DESC,
             COALESCE(sv.effective_from, sv.published_at) DESC NULLS LAST,
             sv.id DESC
    LIMIT 1
) doc_sv ON true
WHERE p.code = 'habilitacion_actividad_economica_expres'
  AND proc_s.code = 'gcba_habilitacion_expres'
  AND NOT EXISTS (
      SELECT 1 FROM public.procedure_documents pd
      WHERE pd.procedure_id = p.id AND pd.document_code = 'CAA'
  );

COMMIT;
