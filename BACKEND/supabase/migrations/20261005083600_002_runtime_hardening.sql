-- Completa la migración inicial de Supabase con la trazabilidad de la caché USIG.
ALTER TABLE public.geocoding_cache
    ADD COLUMN IF NOT EXISTS source_version_id BIGINT
        REFERENCES public.source_versions(id);

UPDATE public.geocoding_cache gc
SET source_version_id = sv.id
FROM public.source_versions sv
JOIN public.sources s ON s.id = sv.source_id
WHERE s.code = 'usig'
  AND sv.status = 'active'
  AND gc.provider = 'USIG'
  AND gc.source_version_id IS NULL;

CREATE INDEX IF NOT EXISTS ix_geocoding_cache_expires_at
    ON public.geocoding_cache (expires_at)
    WHERE expires_at IS NOT NULL;
