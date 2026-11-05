-- ============================================================
-- GESTIÓN INTELIGENTE
-- Completa el contrato de runtime para FastAPI + PostGIS + pgvector
-- y agrega los datos mínimos del vertical slice.
--
-- Requisito previo: habilitar en Supabase las extensiones:
-- postgis, vector, pg_trgm, pgcrypto y unaccent.
-- Supabase recomienda instalar extensiones fuera de `public`, por ejemplo
-- en el esquema `extensions`.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. PARCELAS: soportar historial por source_version
-- ------------------------------------------------------------

ALTER TABLE public.parcels
    DROP CONSTRAINT IF EXISTS parcels_smp_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_parcels_source_smp
    ON public.parcels(source_version_id, smp);

CREATE INDEX IF NOT EXISTS ix_parcels_smp
    ON public.parcels(smp, source_version_id DESC);

-- ------------------------------------------------------------
-- 2. CÓDIGO URBANÍSTICO: columnas utilizadas por TerritoryRepository
-- ------------------------------------------------------------

ALTER TABLE public.urban_parcel_rules
    ADD COLUMN IF NOT EXISTS uni_edif_1 NUMERIC,
    ADD COLUMN IF NOT EXISTS uni_edif_2 NUMERIC,
    ADD COLUMN IF NOT EXISTS uni_edif_3 NUMERIC,
    ADD COLUMN IF NOT EXISTS uni_edif_4 NUMERIC,
    ADD COLUMN IF NOT EXISTS uso_1 INTEGER,
    ADD COLUMN IF NOT EXISTS uso_2 INTEGER,
    ADD COLUMN IF NOT EXISTS uso_3 INTEGER,
    ADD COLUMN IF NOT EXISTS dist_1_grp TEXT,
    ADD COLUMN IF NOT EXISTS dist_1_esp TEXT,
    ADD COLUMN IF NOT EXISTS dist_2_grp TEXT,
    ADD COLUMN IF NOT EXISTS dist_2_esp TEXT,
    ADD COLUMN IF NOT EXISTS dist_3_grp TEXT,
    ADD COLUMN IF NOT EXISTS dist_3_esp TEXT,
    ADD COLUMN IF NOT EXISTS dist_4_grp TEXT,
    ADD COLUMN IF NOT EXISTS dist_4_esp TEXT,
    ADD COLUMN IF NOT EXISTS zona_1 TEXT,
    ADD COLUMN IF NOT EXISTS zona_2 TEXT,
    ADD COLUMN IF NOT EXISTS anac TEXT,
    ADD COLUMN IF NOT EXISTS ci_digital TEXT,
    ADD COLUMN IF NOT EXISTS rh TEXT,
    ADD COLUMN IF NOT EXISTS lep TEXT,
    ADD COLUMN IF NOT EXISTS ensanche TEXT,
    ADD COLUMN IF NOT EXISTS apertura TEXT,
    ADD COLUMN IF NOT EXISTS catalogado TEXT,
    ADD COLUMN IF NOT EXISTS tipo_mza TEXT,
    ADD COLUMN IF NOT EXISTS rivolta TEXT,
    ADD COLUMN IF NOT EXISTS barrio TEXT,
    ADD COLUMN IF NOT EXISTS comuna INTEGER,
    ADD COLUMN IF NOT EXISTS plano_l NUMERIC,
    ADD COLUMN IF NOT EXISTS plano_l_ob TEXT,
    ADD COLUMN IF NOT EXISTS dist_cpu_1 TEXT,
    ADD COLUMN IF NOT EXISTS dist_cpu_2 TEXT,
    ADD COLUMN IF NOT EXISTS fot_em_1 TEXT,
    ADD COLUMN IF NOT EXISTS fot_em_2 TEXT,
    ADD COLUMN IF NOT EXISTS fot_pl_1 TEXT,
    ADD COLUMN IF NOT EXISTS fot_pl_2 TEXT,
    ADD COLUMN IF NOT EXISTS fot_sl_1 TEXT,
    ADD COLUMN IF NOT EXISTS fot_sl_2 TEXT,
    ADD COLUMN IF NOT EXISTS cpu_base TEXT,
    ADD COLUMN IF NOT EXISTS ae_fot_bas TEXT,
    ADD COLUMN IF NOT EXISTS cpu_obs TEXT,
    ADD COLUMN IF NOT EXISTS alicuota NUMERIC,
    ADD COLUMN IF NOT EXISTS inc_uva_21 NUMERIC,
    ADD COLUMN IF NOT EXISTS sm TEXT,
    ADD COLUMN IF NOT EXISTS adps TEXT,
    ADD COLUMN IF NOT EXISTS memo TEXT,
    ADD COLUMN IF NOT EXISTS microcentr TEXT;

-- ------------------------------------------------------------
-- 3. CACHÉ USIG: provenance
-- ------------------------------------------------------------

ALTER TABLE public.geocoding_cache
    ADD COLUMN IF NOT EXISTS source_version_id BIGINT
        REFERENCES public.source_versions(id);

CREATE INDEX IF NOT EXISTS ix_geocoding_cache_expires_at
    ON public.geocoding_cache(expires_at)
    WHERE expires_at IS NOT NULL;

-- ------------------------------------------------------------
-- 4. EMBEDDINGS: leases para ingestion concurrente
-- ------------------------------------------------------------

ALTER TABLE public.document_chunks
    ADD COLUMN IF NOT EXISTS embedding_status TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS embedding_claimed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS embedding_claim_token UUID,
    ADD COLUMN IF NOT EXISTS embedding_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS embedding_error TEXT;

ALTER TABLE public.document_chunks
    DROP CONSTRAINT IF EXISTS document_chunks_embedding_status_check;

ALTER TABLE public.document_chunks
    ADD CONSTRAINT document_chunks_embedding_status_check
    CHECK (embedding_status IN ('pending', 'processing', 'completed', 'failed'));

UPDATE public.document_chunks
SET embedding_status = CASE
    WHEN embedding IS NULL THEN 'pending'
    ELSE 'completed'
END
WHERE embedding_status = 'pending';

CREATE INDEX IF NOT EXISTS ix_query_runs_request_id
    ON public.query_runs(request_id);

CREATE INDEX IF NOT EXISTS ix_chunks_embedding_pending
    ON public.document_chunks(id)
    WHERE embedding IS NULL AND embedding_status IN ('pending', 'failed');

CREATE INDEX IF NOT EXISTS ix_activity_alias_normalized
    ON public.activity_aliases(normalized_alias);

CREATE INDEX IF NOT EXISTS ix_chunks_embedding_claimed
    ON public.document_chunks(embedding_claimed_at)
    WHERE embedding_status = 'processing';

-- ------------------------------------------------------------
-- 5. HISTORIAL DE EVIDENCIA
-- ------------------------------------------------------------

ALTER TABLE public.query_evidence
    DROP CONSTRAINT IF EXISTS query_evidence_document_chunk_id_fkey;

ALTER TABLE public.query_evidence
    ADD CONSTRAINT query_evidence_document_chunk_id_fkey
    FOREIGN KEY (document_chunk_id)
    REFERENCES public.document_chunks(id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_query_evidence_source_version
    ON public.query_evidence(source_version_id);

-- ------------------------------------------------------------
-- 6. DATOS MÍNIMOS DEL VERTICAL SLICE
-- ------------------------------------------------------------

INSERT INTO public.sources(code, name, publisher, canonical_url, description)
VALUES
    ('usig', 'USIG', 'Gobierno de la Ciudad de Buenos Aires',
     'https://ws.usig.buenosaires.gob.ar',
     'Normalización, geocodificación, SMP, datos útiles y reverse geocoding.'),
    ('codigo_urbanistico', 'Código Urbanístico', 'Gobierno de la Ciudad de Buenos Aires',
     'https://data.buenosaires.gob.ar/',
     'Normativa y datos urbanísticos.'),
    ('rus_2022_2024', 'Relevamiento de Usos del Suelo 2022-2024',
     'Gobierno de la Ciudad de Buenos Aires', 'https://data.buenosaires.gob.ar/',
     'Información observacional de usos y actividades.'),
    ('resolucion_96_agc_25', 'Resolución 96/AGC/25',
     'Agencia Gubernamental de Control', NULL,
     'Tramitación de actividades económicas.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.source_versions(source_id, version_label, status, metadata)
SELECT id, 'rest', 'active', '{"kind":"api"}'::jsonb
FROM public.sources
WHERE code = 'usig'
ON CONFLICT (source_id, version_label) DO NOTHING;

INSERT INTO public.source_versions(source_id, version_label, published_at, status, metadata)
SELECT id, '2024-12-31', DATE '2024-12-31', 'ingested', '{"kind":"normative"}'::jsonb
FROM public.sources
WHERE code = 'codigo_urbanistico'
ON CONFLICT (source_id, version_label) DO NOTHING;

INSERT INTO public.source_versions(source_id, version_label, status, metadata)
SELECT id, '2022-2024', 'ingested', '{"kind":"observational"}'::jsonb
FROM public.sources
WHERE code = 'rus_2022_2024'
ON CONFLICT (source_id, version_label) DO NOTHING;

INSERT INTO public.source_versions(
    source_id, version_label, published_at, effective_from, status, metadata
)
SELECT id, '2025-03-14', DATE '2025-03-14', DATE '2025-03-14', 'active',
       '{"resolution":"96/AGC/25"}'::jsonb
FROM public.sources
WHERE code = 'resolucion_96_agc_25'
ON CONFLICT (source_id, version_label) DO NOTHING;

INSERT INTO public.ai_models(provider, model_name, model_type, dimension, is_active)
VALUES
    ('ollama', 'bge-m3', 'embedding', 1024, TRUE),
    ('ollama', 'qwen3:8b', 'chat', NULL, TRUE)
ON CONFLICT (provider, model_name, model_type) DO UPDATE SET
    dimension = EXCLUDED.dimension,
    is_active = EXCLUDED.is_active;

INSERT INTO public.procedures(code, name, description, source_version_id)
SELECT x.code, x.name, x.description, sv.id
FROM (
    VALUES
        ('DDRR_E', 'Declaración Responsable Exprés',
         'Procedimiento de Declaración Responsable Exprés.'),
        ('DDRR_S_P', 'Declaración Responsable Sin Plano',
         'Procedimiento de Declaración Responsable sin plano.'),
        ('DDRR_C_P', 'Declaración Responsable Con Plano',
         'Procedimiento de Declaración Responsable con plano.'),
        ('LICENCIA', 'Licencia', 'Procedimiento de licencia.')
) AS x(code, name, description)
CROSS JOIN (
    SELECT sv.id
    FROM public.source_versions sv
    JOIN public.sources s ON s.id = sv.source_id
    WHERE s.code = 'resolucion_96_agc_25'
      AND sv.version_label = '2025-03-14'
    LIMIT 1
) sv
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.activities(code, name, category, source_version_id, mapping_status)
SELECT '1.5',
       'Alimentación en general y gastronomía',
       '1. COMERCIAL',
       sv.id,
       'official'
FROM public.source_versions sv
JOIN public.sources s ON s.id = sv.source_id
WHERE s.code = 'resolucion_96_agc_25'
  AND sv.version_label = '2025-03-14'
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.activity_aliases(
    activity_id, alias, normalized_alias, status, source_version_id, notes
)
SELECT a.id,
       'cafetería',
       'cafeteria',
       'provisional',
       sv.id,
       'Alias del MVP; debe mantenerse revisable.'
FROM public.activities a
CROSS JOIN (
    SELECT sv.id
    FROM public.source_versions sv
    JOIN public.sources s ON s.id = sv.source_id
    WHERE s.code = 'resolucion_96_agc_25'
      AND sv.version_label = '2025-03-14'
    LIMIT 1
) sv
WHERE a.code = '1.5'
ON CONFLICT (activity_id, normalized_alias) DO NOTHING;

INSERT INTO public.activity_procedures(
    activity_id, procedure_id, source_version_id, priority, notes
)
SELECT a.id,
       p.id,
       sv.id,
       10,
       'Asociación inicial del vertical slice.'
FROM public.activities a
JOIN public.procedures p ON p.code = 'DDRR_C_P'
CROSS JOIN (
    SELECT sv.id
    FROM public.source_versions sv
    JOIN public.sources s ON s.id = sv.source_id
    WHERE s.code = 'resolucion_96_agc_25'
      AND sv.version_label = '2025-03-14'
    LIMIT 1
) sv
WHERE a.code = '1.5'
ON CONFLICT (activity_id, procedure_id, source_version_id) DO NOTHING;

INSERT INTO public.procedure_rules(
    procedure_id,
    source_version_id,
    rule_type,
    priority,
    max_surface_m2,
    conditions,
    rationale
)
SELECT p.id,
       sv.id,
       'eligibility',
       10,
       200,
       '{"requires_no_excluded_complex":true}'::jsonb,
       'Condición documentada para DDRR-E; no implica que 1.5 quede automáticamente en DDRR-E.'
FROM public.procedures p
CROSS JOIN (
    SELECT sv.id
    FROM public.source_versions sv
    JOIN public.sources s ON s.id = sv.source_id
    WHERE s.code = 'resolucion_96_agc_25'
      AND sv.version_label = '2025-03-14'
    LIMIT 1
) sv
WHERE p.code = 'DDRR_E'
  AND NOT EXISTS (
      SELECT 1
      FROM public.procedure_rules pr
      WHERE pr.procedure_id = p.id
        AND pr.rule_type = 'eligibility'
        AND pr.source_version_id = sv.id
  );

UPDATE public.geocoding_cache gc
SET source_version_id = sv.id
FROM public.source_versions sv
JOIN public.sources s ON s.id = sv.source_id
WHERE s.code = 'usig'
  AND sv.version_label = 'rest'
  AND sv.status = 'active'
  AND gc.provider = 'USIG'
  AND gc.source_version_id IS NULL;

INSERT INTO public.geocoding_cache(
    query_key,
    input_address,
    normalized_street,
    street_code,
    height,
    gkba_x,
    gkba_y,
    latitude,
    longitude,
    smp,
    provider,
    provider_version,
    useful_data,
    adjacent_streets,
    reverse_geocoding,
    response_json,
    source_version_id
)
SELECT
    'corrientes|2500',
    'Corrientes 2500',
    'CORRIENTES AV.',
    3174,
    2500,
    105624.672339,
    102713.658996,
    -34.604792,
    -58.401981,
    NULL,
    'USIG',
    'rest+geocoder2.2',
    '{"comuna":"Comuna 3","barrio":"Balvanera","seccion_catastral":"09"}'::jsonb,
    '[{"Codigo":"12065","Nombre":"LARREA"},{"Codigo":"1147","Nombre":"AZCUENAGA"}]'::jsonb,
    '{"verified":true}'::jsonb,
    '{"verified":true,"warnings":[]}'::jsonb,
    sv.id
FROM public.source_versions sv
JOIN public.sources s ON s.id = sv.source_id
WHERE s.code = 'usig'
  AND sv.version_label = 'rest'
  AND sv.status = 'active'
ORDER BY sv.id DESC
LIMIT 1
ON CONFLICT (query_key, provider) DO UPDATE SET
    input_address = EXCLUDED.input_address,
    normalized_street = EXCLUDED.normalized_street,
    street_code = EXCLUDED.street_code,
    height = EXCLUDED.height,
    gkba_x = EXCLUDED.gkba_x,
    gkba_y = EXCLUDED.gkba_y,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    provider_version = EXCLUDED.provider_version,
    useful_data = EXCLUDED.useful_data,
    adjacent_streets = EXCLUDED.adjacent_streets,
    reverse_geocoding = EXCLUDED.reverse_geocoding,
    response_json = EXCLUDED.response_json,
    source_version_id = EXCLUDED.source_version_id,
    fetched_at = NOW(),
    expires_at = NOW() + INTERVAL '24 hours';

COMMIT;
