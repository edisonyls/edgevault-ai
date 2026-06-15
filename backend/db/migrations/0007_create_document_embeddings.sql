CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES resume_uploads (id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0 CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_document_embeddings_upload_chunk UNIQUE (upload_id, chunk_index),
    CONSTRAINT chk_document_embeddings_model_not_empty
        CHECK (length(trim(embedding_model)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_upload_id
    ON document_embeddings (upload_id);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector
    ON document_embeddings USING hnsw (embedding vector_cosine_ops);

ALTER TYPE resume_upload_status ADD VALUE IF NOT EXISTS 'indexing' BEFORE 'processed';
