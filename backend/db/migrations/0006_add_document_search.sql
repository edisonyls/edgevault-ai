-- Full-text search support for document OCR text, plus an index to back
-- date-range filtering on financial records. The search_tsv column is generated
-- from resume_uploads.text so it stays in sync automatically as OCR completes.

ALTER TABLE resume_uploads
    ADD COLUMN IF NOT EXISTS search_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;

CREATE INDEX IF NOT EXISTS idx_resume_uploads_search_tsv
    ON resume_uploads USING GIN (search_tsv);

CREATE INDEX IF NOT EXISTS idx_financial_records_transaction_date
    ON financial_records (transaction_date);
