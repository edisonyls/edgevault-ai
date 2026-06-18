-- Rename the 'processing' upload status to 'extracting'.
--
-- The 'processing' phase corresponds exactly to the OCR/text extraction window
-- (status flips to 'indexing' the moment extraction finishes), so 'extracting'
-- reads as a clearer parallel to the downstream 'indexing' state. Renaming the
-- enum value updates all existing rows in place, so no data backfill is needed.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'resume_upload_status'
          AND e.enumlabel = 'processing'
    ) THEN
        ALTER TYPE resume_upload_status RENAME VALUE 'processing' TO 'extracting';
    END IF;
END $$;
