-- 002_create_api_schedules.sql
-- Create `api_schedules` table to store monitoring schedules per API

CREATE TABLE IF NOT EXISTS public.api_schedules (
    id BIGSERIAL PRIMARY KEY,
    api_id UUID NOT NULL REFERENCES public.monitored_apis (id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    interval_seconds INTEGER NOT NULL CHECK (
        interval_seconds >= 30
        AND interval_seconds <= 1800
    ),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run TIMESTAMP WITHOUT TIME ZONE,
    next_run TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_schedules_tenant ON public.api_schedules (tenant_id);

CREATE INDEX IF NOT EXISTS idx_api_schedules_api ON public.api_schedules (api_id);