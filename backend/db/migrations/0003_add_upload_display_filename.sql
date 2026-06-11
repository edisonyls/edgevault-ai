ALTER TABLE resume_uploads
    ADD COLUMN IF NOT EXISTS display_filename VARCHAR(255);

CREATE OR REPLACE FUNCTION build_resume_upload_display_filename(
    filename TEXT,
    duplicate_index BIGINT
)
RETURNS VARCHAR(255) AS $$
DECLARE
    suffix TEXT := CASE
        WHEN duplicate_index = 0 THEN ''
        ELSE ' (' || duplicate_index || ')'
    END;
    extension TEXT := '';
    stem TEXT := filename;
    reverse_dot_position INTEGER := strpos(reverse(filename), '.');
    max_stem_length INTEGER;
BEGIN
    IF reverse_dot_position > 0
        AND reverse_dot_position < length(filename)
    THEN
        extension := right(filename, reverse_dot_position);
        stem := left(filename, length(filename) - reverse_dot_position);
    END IF;

    IF length(extension) + length(suffix) >= 255 THEN
        extension := right(extension, greatest(0, 255 - length(suffix) - 1));
    END IF;

    max_stem_length := greatest(1, 255 - length(extension) - length(suffix));

    RETURN left(stem, max_stem_length) || suffix || extension;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    upload_record RECORD;
    candidate_filename VARCHAR(255);
    duplicate_index BIGINT;
BEGIN
    CREATE TEMP TABLE tmp_resume_upload_display_filenames (
        display_filename VARCHAR(255) PRIMARY KEY
    ) ON COMMIT DROP;

    INSERT INTO tmp_resume_upload_display_filenames (display_filename)
    SELECT display_filename
    FROM resume_uploads
    WHERE display_filename IS NOT NULL;

    FOR upload_record IN
        SELECT id, original_filename
        FROM resume_uploads
        WHERE display_filename IS NULL
        ORDER BY created_at, id
    LOOP
        duplicate_index := 0;

        LOOP
            candidate_filename := build_resume_upload_display_filename(
                upload_record.original_filename,
                duplicate_index
            );

            BEGIN
                INSERT INTO tmp_resume_upload_display_filenames (display_filename)
                VALUES (candidate_filename);

                UPDATE resume_uploads
                SET display_filename = candidate_filename
                WHERE id = upload_record.id;

                EXIT;
            EXCEPTION WHEN unique_violation THEN
                duplicate_index := duplicate_index + 1;
            END;
        END LOOP;
    END LOOP;
END;
$$;

DROP FUNCTION build_resume_upload_display_filename(TEXT, BIGINT);

ALTER TABLE resume_uploads
    ALTER COLUMN display_filename SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_resume_uploads_display_filename
    ON resume_uploads (display_filename);
