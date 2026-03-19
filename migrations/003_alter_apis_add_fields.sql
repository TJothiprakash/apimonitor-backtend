-- 003_alter_apis_add_fields.sql
-- Optional: augment existing `apis` table (use only if you prefer to reuse existing table)

-- Add columns if they do not already exist
ALTER TABLE public.apis
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS payload TEXT,
ADD COLUMN IF NOT EXISTS payload_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS headers JSONB,
ADD COLUMN IF NOT EXISTS interval_seconds INTEGER;

-- Create useful indexes
CREATE INDEX IF NOT EXISTS idx_apis_tenant ON public.apis (tenant_id);

CREATE INDEX IF NOT EXISTS idx_apis_name ON public.apis (name);

-- If you want to enforce allowed interval range, add a constraint (optional):
-- ALTER TABLE public.apis ADD CONSTRAINT chk_apis_interval_seconds CHECK (interval_seconds IS NULL OR (interval_seconds >= 30 AND interval_seconds <= 1800));