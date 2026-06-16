-- Scope corrections to a workspace, consistent with resume_uploads /
-- vendor_rules / assistant_queries. Without this, demo-workspace corrections
-- would mix into the owner's training/eval dataset.

ALTER TABLE extraction_corrections
    ADD COLUMN IF NOT EXISTS workspace_id UUID;

-- Backfill from the owning upload; every correction references a resume_upload,
-- which already carries the workspace after migration 0011.
UPDATE extraction_corrections ec
SET workspace_id = ru.workspace_id
FROM resume_uploads ru
WHERE ru.id = ec.upload_id
  AND ec.workspace_id IS NULL;

ALTER TABLE extraction_corrections
    ALTER COLUMN workspace_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_extraction_corrections_workspace_id'
    ) THEN
        ALTER TABLE extraction_corrections
            ADD CONSTRAINT fk_extraction_corrections_workspace_id
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_extraction_corrections_workspace_created_at
    ON extraction_corrections (workspace_id, created_at DESC);
