-- Append-only log of natural-language assistant questions and the answers the
-- controlled query engine returned. query_type records which rule-based intent
-- handled the question (or 'unknown' when none matched), so we can review what
-- people ask and which intents are missing.

CREATE TABLE IF NOT EXISTS assistant_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    query_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_assistant_queries_question_not_empty
        CHECK (length(trim(question)) > 0),
    CONSTRAINT chk_assistant_queries_query_type_not_empty
        CHECK (length(trim(query_type)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_assistant_queries_created_at
    ON assistant_queries (created_at DESC);
