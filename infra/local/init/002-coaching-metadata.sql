ALTER TABLE coaching_source ADD COLUMN IF NOT EXISTS source_version text;
ALTER TABLE coaching_source ADD COLUMN IF NOT EXISTS body_region_tags text[] NOT NULL DEFAULT '{}';
ALTER TABLE coaching_source ADD COLUMN IF NOT EXISTS audience text;
ALTER TABLE coaching_source ADD COLUMN IF NOT EXISTS skill_level text;
ALTER TABLE coaching_source ADD COLUMN IF NOT EXISTS page_locator text;

ALTER TABLE coaching_chunk ADD COLUMN IF NOT EXISTS source_version text;
ALTER TABLE coaching_chunk ADD COLUMN IF NOT EXISTS body_region_tags text[] NOT NULL DEFAULT '{}';
ALTER TABLE coaching_chunk ADD COLUMN IF NOT EXISTS audience text;
ALTER TABLE coaching_chunk ADD COLUMN IF NOT EXISTS skill_level text;
ALTER TABLE coaching_chunk ADD COLUMN IF NOT EXISTS page_locator text;
