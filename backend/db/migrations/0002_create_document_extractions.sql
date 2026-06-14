DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'document_extraction_method'
    ) THEN
        CREATE TYPE document_extraction_method AS ENUM (
            'pdf_text_layer',
            'ocr'
        );
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'document_extraction_status'
    ) THEN
        CREATE TYPE document_extraction_status AS ENUM (
            'succeeded',
            'failed'
        );
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES resume_uploads (id) ON DELETE CASCADE,
    raw_text TEXT,
    ocr_engine TEXT NOT NULL,
    ocr_engine_version TEXT,
    extraction_method document_extraction_method,
    ocr_confidence REAL CHECK (ocr_confidence >= 0 AND ocr_confidence <= 100),
    page_count INTEGER CHECK (page_count >= 0),
    processing_latency_ms INTEGER NOT NULL CHECK (processing_latency_ms >= 0),
    status document_extraction_status NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_document_extractions_ocr_engine_not_empty
        CHECK (length(trim(ocr_engine)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_document_extractions_upload_id
    ON document_extractions (upload_id);

CREATE INDEX IF NOT EXISTS idx_document_extractions_upload_created_at
    ON document_extractions (upload_id, created_at DESC);
