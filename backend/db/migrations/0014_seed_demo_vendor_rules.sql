-- Seed the demo workspace with the same baseline vendor rules as owner.
--
-- The original seed (0005) ran before workspaces existed, and 0011 backfilled
-- every rule to the owner workspace, leaving demo with none. Because the
-- extraction engine has no code-level fallback and matches only against
-- workspace-scoped rows (financial_extraction._load_vendor_rules), the demo
-- workspace categorised every document as "other". These are generic vendor
-- keywords (reference config, not personal data), so it is safe to duplicate
-- them into demo. Idempotent via the (workspace_id, keyword) unique index.

INSERT INTO vendor_rules (workspace_id, keyword, vendor, category) VALUES
    ('00000000-0000-4000-8000-000000000002', 'woolworths', 'Woolworths', 'groceries'),
    ('00000000-0000-4000-8000-000000000002', 'coles', 'Coles', 'groceries'),
    ('00000000-0000-4000-8000-000000000002', 'aldi', 'ALDI', 'groceries'),
    ('00000000-0000-4000-8000-000000000002', 'iga', 'IGA', 'groceries'),
    ('00000000-0000-4000-8000-000000000002', 'agl', 'AGL', 'utilities'),
    ('00000000-0000-4000-8000-000000000002', 'origin energy', 'Origin Energy', 'utilities'),
    ('00000000-0000-4000-8000-000000000002', 'energyaustralia', 'EnergyAustralia', 'utilities'),
    ('00000000-0000-4000-8000-000000000002', 'energy australia', 'EnergyAustralia', 'utilities'),
    ('00000000-0000-4000-8000-000000000002', 'telstra', 'Telstra', 'internet_phone'),
    ('00000000-0000-4000-8000-000000000002', 'optus', 'Optus', 'internet_phone'),
    ('00000000-0000-4000-8000-000000000002', 'tpg', 'TPG', 'internet_phone'),
    ('00000000-0000-4000-8000-000000000002', 'aussie broadband', 'Aussie Broadband', 'internet_phone'),
    ('00000000-0000-4000-8000-000000000002', 'vodafone', 'Vodafone', 'internet_phone'),
    ('00000000-0000-4000-8000-000000000002', 'myki', 'Myki', 'transport'),
    ('00000000-0000-4000-8000-000000000002', 'uber', 'Uber', 'transport'),
    ('00000000-0000-4000-8000-000000000002', 'didi', 'DiDi', 'transport'),
    ('00000000-0000-4000-8000-000000000002', 'netflix', 'Netflix', 'subscription'),
    ('00000000-0000-4000-8000-000000000002', 'spotify', 'Spotify', 'subscription'),
    ('00000000-0000-4000-8000-000000000002', 'chatgpt', 'ChatGPT', 'subscription'),
    ('00000000-0000-4000-8000-000000000002', 'openai', 'OpenAI', 'subscription'),
    ('00000000-0000-4000-8000-000000000002', 'apple', 'Apple', 'subscription')
ON CONFLICT (workspace_id, keyword) DO NOTHING;
