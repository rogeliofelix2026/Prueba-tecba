BEGIN;

-- Esquema normalizado estable para el MVP. En una instalación nueva estas
-- columnas todavía no existen; en una instalación que ya cargó el dataset,
-- la migración solo las conserva y descarta el resto.
ALTER TABLE public.urban_parcel_rules
    ADD COLUMN IF NOT EXISTS uso_1 INTEGER,
    ADD COLUMN IF NOT EXISTS uso_2 INTEGER,
    ADD COLUMN IF NOT EXISTS uso_3 INTEGER,
    ADD COLUMN IF NOT EXISTS zona_1 TEXT,
    ADD COLUMN IF NOT EXISTS zona_2 TEXT,
    ADD COLUMN IF NOT EXISTS barrio TEXT,
    ADD COLUMN IF NOT EXISTS comuna INTEGER,
    ADD COLUMN IF NOT EXISTS cpu_base TEXT,
    ADD COLUMN IF NOT EXISTS cpu_obs TEXT;

-- Si la tabla proviene del dataset completo, verificamos que los campos que
-- vamos a eliminar ya estén cubiertos por raw. En una instalación nueva no
-- existen esos campos y esta sección se omite.
DO $$
DECLARE
    unsafe_rows BIGINT;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'urban_parcel_rules'
          AND column_name = 'uni_edif_1'
    ) THEN
        EXECUTE $sql$
            SELECT COUNT(*)
            FROM public.urban_parcel_rules
            WHERE (
                  (uni_edif_1 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'uni_edif_1')) OR
                  (uni_edif_2 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'uni_edif_2')) OR
                  (uni_edif_3 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'uni_edif_3')) OR
                  (uni_edif_4 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'uni_edif_4')) OR
                  (dist_1_grp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_1_grp')) OR
                  (dist_1_esp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_1_esp')) OR
                  (dist_2_grp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_2_grp')) OR
                  (dist_2_esp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_2_esp')) OR
                  (dist_3_grp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_3_grp')) OR
                  (dist_3_esp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_3_esp')) OR
                  (dist_4_grp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_4_grp')) OR
                  (dist_4_esp IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_4_esp')) OR
                  (anac IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'anac')) OR
                  (ci_digital IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'ci_digital')) OR
                  (rh IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'rh')) OR
                  (lep IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'lep')) OR
                  (ensanche IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'ensanche')) OR
                  (apertura IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'apertura')) OR
                  (catalogado IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'catalogado')) OR
                  (tipo_mza IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'tipo_mza')) OR
                  (rivolta IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'rivolta')) OR
                  (plano_l IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'plano_l')) OR
                  (plano_l_ob IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'plano_l_ob')) OR
                  (dist_cpu_1 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_cpu_1')) OR
                  (dist_cpu_2 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'dist_cpu_2')) OR
                  (fot_em_1 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_em_1')) OR
                  (fot_em_2 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_em_2')) OR
                  (fot_pl_1 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_pl_1')) OR
                  (fot_pl_2 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_pl_2')) OR
                  (fot_sl_1 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_sl_1')) OR
                  (fot_sl_2 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'fot_sl_2')) OR
                  (ae_fot_bas IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'ae_fot_bas')) OR
                  (alicuota IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'alicuota')) OR
                  (inc_uva_21 IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'inc_uva_21')) OR
                  (sm IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'sm')) OR
                  (adps IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'adps')) OR
                  (memo IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'memo')) OR
                  (microcentr IS NOT NULL AND NOT (COALESCE(raw, '{}'::jsonb) ? 'microcentr'))

              )
        $sql$ INTO unsafe_rows;

        IF unsafe_rows > 0 THEN
            RAISE EXCEPTION
                'No se puede simplificar urban_parcel_rules: % filas tienen datos fuera de raw.',
                unsafe_rows;
        END IF;
    END IF;
END $$;

ALTER TABLE public.urban_parcel_rules
    DROP COLUMN IF EXISTS uni_edif_1,
    DROP COLUMN IF EXISTS uni_edif_2,
    DROP COLUMN IF EXISTS uni_edif_3,
    DROP COLUMN IF EXISTS uni_edif_4,
    DROP COLUMN IF EXISTS dist_1_grp,
    DROP COLUMN IF EXISTS dist_1_esp,
    DROP COLUMN IF EXISTS dist_2_grp,
    DROP COLUMN IF EXISTS dist_2_esp,
    DROP COLUMN IF EXISTS dist_3_grp,
    DROP COLUMN IF EXISTS dist_3_esp,
    DROP COLUMN IF EXISTS dist_4_grp,
    DROP COLUMN IF EXISTS dist_4_esp,
    DROP COLUMN IF EXISTS anac,
    DROP COLUMN IF EXISTS ci_digital,
    DROP COLUMN IF EXISTS rh,
    DROP COLUMN IF EXISTS lep,
    DROP COLUMN IF EXISTS ensanche,
    DROP COLUMN IF EXISTS apertura,
    DROP COLUMN IF EXISTS catalogado,
    DROP COLUMN IF EXISTS tipo_mza,
    DROP COLUMN IF EXISTS rivolta,
    DROP COLUMN IF EXISTS plano_l,
    DROP COLUMN IF EXISTS plano_l_ob,
    DROP COLUMN IF EXISTS dist_cpu_1,
    DROP COLUMN IF EXISTS dist_cpu_2,
    DROP COLUMN IF EXISTS fot_em_1,
    DROP COLUMN IF EXISTS fot_em_2,
    DROP COLUMN IF EXISTS fot_pl_1,
    DROP COLUMN IF EXISTS fot_pl_2,
    DROP COLUMN IF EXISTS fot_sl_1,
    DROP COLUMN IF EXISTS fot_sl_2,
    DROP COLUMN IF EXISTS ae_fot_bas,
    DROP COLUMN IF EXISTS alicuota,
    DROP COLUMN IF EXISTS inc_uva_21,
    DROP COLUMN IF EXISTS sm,
    DROP COLUMN IF EXISTS adps,
    DROP COLUMN IF EXISTS memo,
    DROP COLUMN IF EXISTS microcentr;

COMMENT ON TABLE public.urban_parcel_rules IS
    'Datos urbanísticos normalizados para el MVP. La fuente original completa se conserva en raw.';

COMMIT;
