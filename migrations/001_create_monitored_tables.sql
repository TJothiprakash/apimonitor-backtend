-- 001_create_monitored_tables.sql
-- Create `monitored_apis` and `api_logs` tables for API registration and logs

CREATE TABLE IF NOT EXISTS public.monitored_apis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    tenant_id UUID NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    payload TEXT,
    payload_type VARCHAR(50), -- e.g. 'json', 'form', 'raw'
    headers JSONB, -- optional HTTP headers to include
    timeout_ms INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_monitored_apis_tenant ON public.monitored_apis (tenant_id);

CREATE INDEX IF NOT EXISTS idx_monitored_apis_name ON public.monitored_apis (name);

-- Logs for monitored API invocations
CREATE TABLE IF NOT EXISTS public.api_logs (
    id BIGSERIAL PRIMARY KEY,
    api_id UUID NOT NULL REFERENCES public.monitored_apis (id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    status_code INTEGER,
    response_time_ms NUMERIC,
    success BOOLEAN,
    error_message TEXT,
    response_body TEXT,
    checked_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_logs_api ON public.api_logs (api_id);

CREATE INDEX IF NOT EXISTS idx_api_logs_tenant ON public.api_logs (tenant_id);

-- Notes:
-- This creates a fresh set of tables so existing `apis` and `api_results` tables are untouched.