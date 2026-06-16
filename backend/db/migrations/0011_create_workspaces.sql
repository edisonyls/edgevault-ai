CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    read_only BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_workspaces_key_not_empty
        CHECK (length(trim(key)) > 0),
    CONSTRAINT chk_workspaces_display_name_not_empty
        CHECK (length(trim(display_name)) > 0)
);

INSERT INTO workspaces (id, key, display_name, read_only)
VALUES
    ('00000000-0000-4000-8000-000000000001', 'owner', 'Personal', false),
    ('00000000-0000-4000-8000-000000000002', 'demo', 'Demo', false)
ON CONFLICT (id) DO UPDATE SET
    key = EXCLUDED.key,
    display_name = EXCLUDED.display_name,
    read_only = EXCLUDED.read_only;

ALTER TABLE resume_uploads
    ADD COLUMN IF NOT EXISTS workspace_id UUID;

UPDATE resume_uploads
SET workspace_id = '00000000-0000-4000-8000-000000000001'
WHERE workspace_id IS NULL;

ALTER TABLE resume_uploads
    ALTER COLUMN workspace_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_resume_uploads_workspace_id'
    ) THEN
        ALTER TABLE resume_uploads
            ADD CONSTRAINT fk_resume_uploads_workspace_id
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_resume_uploads_workspace_created_at
    ON resume_uploads (workspace_id, created_at DESC);

DROP INDEX IF EXISTS idx_resume_uploads_display_filename;

CREATE UNIQUE INDEX IF NOT EXISTS idx_resume_uploads_workspace_display_filename
    ON resume_uploads (workspace_id, display_filename);

ALTER TABLE vendor_rules
    ADD COLUMN IF NOT EXISTS workspace_id UUID;

UPDATE vendor_rules
SET workspace_id = '00000000-0000-4000-8000-000000000001'
WHERE workspace_id IS NULL;

ALTER TABLE vendor_rules
    ALTER COLUMN workspace_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_vendor_rules_workspace_id'
    ) THEN
        ALTER TABLE vendor_rules
            ADD CONSTRAINT fk_vendor_rules_workspace_id
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id);
    END IF;
END
$$;

ALTER TABLE vendor_rules
    DROP CONSTRAINT IF EXISTS vendor_rules_keyword_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vendor_rules_workspace_keyword
    ON vendor_rules (workspace_id, keyword);

CREATE INDEX IF NOT EXISTS idx_vendor_rules_workspace_updated_at
    ON vendor_rules (workspace_id, updated_at DESC);

ALTER TABLE assistant_queries
    ADD COLUMN IF NOT EXISTS workspace_id UUID;

UPDATE assistant_queries
SET workspace_id = '00000000-0000-4000-8000-000000000001'
WHERE workspace_id IS NULL;

ALTER TABLE assistant_queries
    ALTER COLUMN workspace_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_assistant_queries_workspace_id'
    ) THEN
        ALTER TABLE assistant_queries
            ADD CONSTRAINT fk_assistant_queries_workspace_id
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_assistant_queries_workspace_created_at
    ON assistant_queries (workspace_id, created_at DESC);
