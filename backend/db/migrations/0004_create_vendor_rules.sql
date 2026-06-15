-- User-learned vendor categorisation rules. When a user manually corrects a
-- record's vendor/category, we persist a keyword -> vendor, category rule here
-- so future documents containing that keyword are categorised automatically.
-- These rules take precedence over the built-in VENDOR_RULES in code.

CREATE TABLE IF NOT EXISTS vendor_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL UNIQUE,
    vendor TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_vendor_rules_keyword_not_empty
        CHECK (length(trim(keyword)) > 0),
    CONSTRAINT chk_vendor_rules_vendor_not_empty
        CHECK (length(trim(vendor)) > 0),
    CONSTRAINT chk_vendor_rules_category_not_empty
        CHECK (length(trim(category)) > 0)
);

CREATE OR REPLACE FUNCTION set_vendor_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_vendor_rules_updated_at ON vendor_rules;

CREATE TRIGGER trg_vendor_rules_updated_at
BEFORE UPDATE ON vendor_rules
FOR EACH ROW
EXECUTE FUNCTION set_vendor_rules_updated_at();
