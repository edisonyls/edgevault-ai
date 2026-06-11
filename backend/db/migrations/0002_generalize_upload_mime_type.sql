ALTER TABLE resume_uploads
    ALTER COLUMN mime_type TYPE TEXT
    USING mime_type::TEXT;

DROP TYPE IF EXISTS resume_upload_mime_type;

ALTER TABLE resume_uploads
    ADD CONSTRAINT chk_resume_uploads_mime_type_not_empty
    CHECK (length(trim(mime_type)) > 0);
