-- Append-only log of every manual correction a user makes to a financial
-- record. Each row is one labelled training example: `predicted` is what the
-- extractor produced, `corrected` is the ground truth after the user's edit,
-- and `changed_fields` records exactly which fields the user had to fix.
--
-- This is the data flywheel: corrections used to be discarded (the record was
-- overwritten in place), so no dataset could accumulate. Capturing them here
-- feeds both offline evaluation and downstream retrieval / fine-tuning.

CREATE TABLE IF NOT EXISTS extraction_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES resume_uploads (id) ON DELETE CASCADE,
    financial_record_id UUID NOT NULL REFERENCES financial_records (id) ON DELETE CASCADE,
    -- Snapshot of the record's fields before this correction was applied.
    predicted JSONB NOT NULL,
    -- Snapshot of the record's fields after this correction was applied.
    corrected JSONB NOT NULL,
    -- Field names whose value actually changed in this correction.
    changed_fields TEXT[] NOT NULL DEFAULT '{}',
    -- The extraction_method that produced `predicted` (e.g. 'rules_v1').
    extraction_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_extraction_corrections_method_not_empty
        CHECK (length(trim(extraction_method)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_extraction_corrections_upload_id
    ON extraction_corrections (upload_id);

CREATE INDEX IF NOT EXISTS idx_extraction_corrections_created_at
    ON extraction_corrections (created_at DESC);
