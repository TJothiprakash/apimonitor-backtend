-- 005_add_tenant_id_api_schedules.sql
-- Backfill/repair migration for environments that already have `api_schedules` table
-- but are missing the `tenant_id` column.
--
-- Why:
-- - Scheduler loop and schedule endpoint both expect `api_schedules.tenant_id`.
-- - Some DBs may have an older version of the table created without tenant_id.
--
-- Postgres:
-- 1) Add tenant_id column if missing
ALTER TABLE public.api_schedules
ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- 2) Backfill tenant_id from monitored_apis.tenant_id
UPDATE public.api_schedules s
SET
    tenant_id = a.tenant_id
FROM public.monitored_apis a
WHERE
    s.api_id = a.id
    AND s.tenant_id IS NULL;

-- 3) Add FK constraint (only if it doesn't already exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_api_schedules_tenant_id'
    ) THEN
        ALTER TABLE public.api_schedules
        ADD CONSTRAINT fk_api_schedules_tenant_id
        FOREIGN KEY (tenant_id)
        REFERENCES public.tenants (id)
        ON DELETE CASCADE;
    END IF;
END $$;

-- 4) Enforce NOT NULL after backfill (will fail if you have orphan schedule rows)
ALTER TABLE public.api_schedules ALTER COLUMN tenant_id SET NOT NULL;

-- 5) Add index
CREATE INDEX IF NOT EXISTS idx_api_schedules_tenant ON public.api_schedules (tenant_id);