-- Records which tier of the intent resolver answered each question: the
-- rule-based parser, the local NPU model, or the cloud fallback. Lets us see
-- how often each tier fires and whether the local model is pulling its weight.

ALTER TABLE assistant_queries
    ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'rules';
