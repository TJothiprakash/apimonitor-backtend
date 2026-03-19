-- Migration: Add `end_at` column to `api_schedules`
-- Postgres (preferred):
ALTER TABLE api_schedules
ADD COLUMN IF NOT EXISTS end_at TIMESTAMP
WITH
    TIME ZONE NULL;

-- SQLite alternative (uncomment and run if using sqlite):
-- ALTER TABLE api_schedules ADD COLUMN end_at DATETIME NULL;

-- Notes:
-- - This migration adds a nullable `end_at` column. Existing schedules will remain unchanged.
-- - After running the migration, restart the application so SQLAlchemy sees the new column.