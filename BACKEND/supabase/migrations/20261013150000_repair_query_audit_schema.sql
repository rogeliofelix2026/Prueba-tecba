-- SGI v0.3.5: hacer explícito el contrato de auditoría del flujo determinista.
-- Incremental e idempotente. No elimina datos, tablas ni columnas antiguas.
-- Aplicar después de revisar el historial de migraciones y contar con backup/staging.
BEGIN;

ALTER TABLE public.query_runs
    ADD COLUMN IF NOT EXISTS request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    ADD COLUMN IF NOT EXISTS response_json JSONB,
    ADD COLUMN IF NOT EXISTS execution_mode TEXT NOT NULL DEFAULT 'legacy';

UPDATE public.query_runs
SET request_payload = '{}'::JSONB
WHERE request_payload IS NULL;

ALTER TABLE public.query_runs
    ALTER COLUMN request_payload SET DEFAULT '{}'::JSONB,
    ALTER COLUMN request_payload SET NOT NULL,
    ALTER COLUMN execution_mode SET DEFAULT 'legacy',
    ALTER COLUMN execution_mode SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.query_runs'::regclass
          AND conname = 'ck_query_runs_execution_mode'
    ) THEN
        ALTER TABLE public.query_runs
            ADD CONSTRAINT ck_query_runs_execution_mode
            CHECK (execution_mode IN ('legacy', 'deterministic', 'ai_assisted'));
    END IF;
END $$;

-- El esquema legacy solo registraba la fuente o el chunk. Estas columnas permiten
-- guardar trazabilidad determinista para reglas de uso, zonificación y procedimiento.
ALTER TABLE public.query_evidence
    ADD COLUMN IF NOT EXISTS activity_use_rule_id BIGINT
        REFERENCES public.activity_use_rules(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS urban_parcel_rule_id BIGINT
        REFERENCES public.urban_parcel_rules(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS procedure_rule_id BIGINT
        REFERENCES public.procedure_rules(id) ON DELETE SET NULL;

-- En el esquema inicial reference_key era NOT NULL; las referencias nuevas se guardan
-- como FK tipadas. Lo dejamos nullable para no romper inserciones legacy de RAG/IA;
-- cuando la columna existe, record_territory_result la rellena en cada evidencia.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'query_evidence'
          AND column_name = 'reference_key'
    ) THEN
        ALTER TABLE public.query_evidence ALTER COLUMN reference_key DROP NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_query_runs_status_started
    ON public.query_runs(status, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_query_evidence_query
    ON public.query_evidence(query_run_id);
CREATE INDEX IF NOT EXISTS ix_query_evidence_source
    ON public.query_evidence(source_version_id)
    WHERE source_version_id IS NOT NULL;

COMMENT ON COLUMN public.query_runs.request_payload IS
    'Entrada estructurada del flujo determinista, incluidas actividad, dirección y parámetros.';
COMMENT ON COLUMN public.query_runs.response_json IS
    'Respuesta estructurada del endpoint para trazabilidad y control de calidad.';
COMMENT ON COLUMN public.query_runs.execution_mode IS
    'Modo de ejecución: legacy, deterministic o ai_assisted.';

COMMIT;
