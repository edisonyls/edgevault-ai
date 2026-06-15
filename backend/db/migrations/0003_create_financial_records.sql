-- Structured financial data extracted from a document's OCR text. One record
-- per upload; the rules engine creates it and users can manually correct it.

CREATE TABLE IF NOT EXISTS financial_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL UNIQUE REFERENCES resume_uploads (id) ON DELETE CASCADE,
    document_type TEXT,
    vendor TEXT,
    transaction_date DATE,
    due_date DATE,
    total_amount NUMERIC(14, 2) CHECK (total_amount >= 0),
    currency TEXT NOT NULL DEFAULT 'AUD',
    category TEXT,
    payment_status TEXT,
    extraction_method TEXT NOT NULL,
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_financial_records_extraction_method_not_empty
        CHECK (length(trim(extraction_method)) > 0),
    CONSTRAINT chk_financial_records_currency_not_empty
        CHECK (length(trim(currency)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_financial_records_upload_id
    ON financial_records (upload_id);

CREATE INDEX IF NOT EXISTS idx_financial_records_created_at
    ON financial_records (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_records_category
    ON financial_records (category);

CREATE OR REPLACE FUNCTION set_financial_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_financial_records_updated_at ON financial_records;

CREATE TRIGGER trg_financial_records_updated_at
BEFORE UPDATE ON financial_records
FOR EACH ROW
EXECUTE FUNCTION set_financial_records_updated_at();
