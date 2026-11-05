-- Diagnóstico de solo lectura: códigos de clasificación vs. códigos canónicos de variante.
-- Ejecutar en Supabase SQL Editor en el entorno correcto. No modifica datos.

-- 1. Valores presentes en procedure_variants. Una misma denominación puede aparecer
-- en más de un procedimiento; revisar el procedimiento padre y la procedencia.
SELECT
    p.code AS procedure_code,
    p.name AS procedure_name,
    pv.id AS procedure_variant_id,
    pv.code AS variant_code,
    pv.name AS variant_name,
    pv.procedure_id,
    pv.source_version_id
FROM public.procedure_variants pv
JOIN public.procedures p ON p.id = pv.procedure_id
WHERE pv.code IN (
    'DDRR_CP', 'DDRR_SP', 'DDRR_E', 'DDRR_CON_PLANO', 'DDRR_SIN_PLANO', 'LICENCIA'
)
ORDER BY p.code, pv.code;

-- 2. Comparación entre los códigos que puede producir Anexo II y los códigos de
-- variante que el repositorio espera. Una fila sin count_variant indica posible mismatch.
WITH expected(mapping_code, canonical_variant_code) AS (
    VALUES
        ('DDRR_CP', 'DDRR_CON_PLANO'),
        ('DDRR_SP', 'DDRR_SIN_PLANO'),
        ('DDRR_E', 'DDRR_E'),
        ('LICENCIA', 'LICENCIA')
), variants AS (
    SELECT pv.code, COUNT(*) AS variant_count
    FROM public.procedure_variants pv
    JOIN public.source_versions sv ON sv.id = pv.source_version_id
    WHERE sv.status IN ('active', 'ingested')
    GROUP BY pv.code
)
SELECT e.mapping_code, e.canonical_variant_code,
       COALESCE(v.variant_count, 0) AS active_or_ingested_variant_count
FROM expected e
LEFT JOIN variants v ON v.code = e.canonical_variant_code
ORDER BY e.mapping_code;

-- 3. Volumen de clasificaciones Anexo II que dependen de cada código.
SELECT atm.procedure_type_code, atm.mapping_status, COUNT(*) AS activity_mapping_count
FROM public.activity_tramite_mappings atm
JOIN public.source_versions sv ON sv.id = atm.source_version_id
WHERE sv.status IN ('active', 'ingested')
GROUP BY atm.procedure_type_code, atm.mapping_status
ORDER BY atm.procedure_type_code, atm.mapping_status;

-- Importante: si el código corto y el canónico existen a la vez, no borrar ni renombrar
-- filas automáticamente. Revisar si son duplicados por procedimiento, source_version_id
-- y condiciones antes de preparar una migración de reparación.
