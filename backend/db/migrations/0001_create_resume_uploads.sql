CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'resume_upload_mime_type'
    ) THEN
        CREATE TYPE resume_upload_mime_type AS ENUM (
            'application/pdf'
        );
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'resume_upload_status'
    ) THEN
        CREATE TYPE resume_upload_status AS ENUM (
            'uploaded',
            'processing',
            'processed',
            'failed'
        );
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS resume_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL UNIQUE,
    file_path TEXT,
    mime_type resume_upload_mime_type NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size >= 0),
    status resume_upload_status NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resume_uploads_status
    ON resume_uploads (status);

CREATE INDEX IF NOT EXISTS idx_resume_uploads_created_at
    ON resume_uploads (created_at DESC);

CREATE OR REPLACE FUNCTION set_resume_uploads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_resume_uploads_updated_at ON resume_uploads;

CREATE TRIGGER trg_resume_uploads_updated_at
BEFORE UPDATE ON resume_uploads
FOR EACH ROW
EXECUTE FUNCTION set_resume_uploads_updated_at();
