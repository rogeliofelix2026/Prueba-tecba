-- ============================================================
-- Recuperación de SMP en caché USIG
-- ============================================================

BEGIN;

UPDATE public.geocoding_cache
SET smp = reverse_geocoding->>'parcela'
WHERE smp IS NULL
  AND jsonb_typeof(reverse_geocoding) = 'object'
  AND reverse_geocoding ? 'parcela'
  AND reverse_geocoding->>'parcela' ~ '^[0-9]{2,3}-[^-]+-[^-]+$';

COMMIT;
