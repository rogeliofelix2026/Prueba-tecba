BEGIN;

ALTER TABLE public.document_chunks
    ADD COLUMN IF NOT EXISTS embedding_status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE public.document_chunks
    DROP CONSTRAINT IF EXISTS document_chunks_embedding_status_check;

ALTER TABLE public.document_chunks
    ADD CONSTRAINT document_chunks_embedding_status_check
    CHECK (embedding_status IN ('pending', 'processing', 'completed', 'failed'));

ALTER TABLE public.document_chunks
    ADD COLUMN IF NOT EXISTS embedding_claimed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS embedding_claim_token UUID,
    ADD COLUMN IF NOT EXISTS embedding_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS embedding_error TEXT;

UPDATE public.document_chunks
SET embedding_status = CASE
    WHEN embedding IS NULL THEN 'pending'
    ELSE 'completed'
END
WHERE embedding_status = 'pending';

CREATE INDEX IF NOT EXISTS ix_query_runs_request_id
    ON public.query_runs(request_id);

CREATE INDEX IF NOT EXISTS ix_chunks_embedding_pending
    ON public.document_chunks (id)
    WHERE embedding IS NULL
      AND embedding_status IN ('pending', 'failed');

CREATE INDEX IF NOT EXISTS ix_chunks_embedding_claimed
    ON public.document_chunks (embedding_claimed_at)
    WHERE embedding_status = 'processing';

COMMIT;
