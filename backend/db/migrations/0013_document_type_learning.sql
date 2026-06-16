-- Document-type learning.
--
-- 1. document_type_rules: user-learned document-type rules. When a user
--    corrects a record's document_type (e.g. receipt -> invoice), we persist a
--    keyword -> document_type rule here, keyed by the record's vendor, so future
--    documents mentioning that vendor are classified the same way. These learned
--    rules only fill in documents whose text states no type of their own.
--
-- 2. financial_records.document_type_source: records how a record's
--    document_type was determined:
--      'document' -> read from explicit wording in the OCR text (source of truth)
--      'learned'  -> filled in from a learned rule above
--      'default'  -> a best-guess fallback when the document said nothing
--    This lets the UI show the basis for the type and lets the learning loop
--    avoid creating vendor-wide rules from corrections to self-labelled
--    documents. Existing rows predate the signal and stay NULL.

CREATE TABLE IF NOT EXISTS document_type_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    keyword TEXT NOT NULL,
    document_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_document_type_rules_keyword_not_empty
        CHECK (length(trim(keyword)) > 0),
    CONSTRAINT chk_document_type_rules_document_type_not_empty
        CHECK (length(trim(document_type)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_type_rules_workspace_keyword
    ON document_type_rules (workspace_id, keyword);

CREATE INDEX IF NOT EXISTS idx_document_type_rules_workspace_updated_at
    ON document_type_rules (workspace_id, updated_at DESC);

CREATE OR REPLACE FUNCTION set_document_type_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_document_type_rules_updated_at ON document_type_rules;

CREATE TRIGGER trg_document_type_rules_updated_at
BEFORE UPDATE ON document_type_rules
FOR EACH ROW
EXECUTE FUNCTION set_document_type_rules_updated_at();

ALTER TABLE financial_records
    ADD COLUMN IF NOT EXISTS document_type_source TEXT;
