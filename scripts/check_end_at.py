#!/usr/bin/env python3
"""
Check that the 'end_at' column exists in the `api_schedules` table.
Usage: python scripts/check_end_at.py
"""
import sys
from sqlalchemy import create_engine, inspect
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

try:
    cols = [c['name'] for c in inspector.get_columns('api_schedules')]
except Exception as e:
    print(f"ERROR: failed to inspect table 'api_schedules': {e}")
    sys.exit(2)

if 'end_at' in cols:
    print("OK: 'end_at' column exists in 'api_schedules'")
    sys.exit(0)
else:
    print("MISSING: 'end_at' column NOT found in 'api_schedules'")
    print("Run the SQL in migrations/004_add_end_at_api_schedules.sql or apply the appropriate ALTER TABLE for your DB.")
    sys.exit(1)
