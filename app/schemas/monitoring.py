from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

class MonitoredAPICreate(BaseModel):
    name: str = Field(..., max_length=255)
    url: str
    description: Optional[str] = None
    method: Optional[str] = "GET"
    payload: Optional[str] = None
    payload_type: Optional[str] = None
    headers: Optional[dict] = None
    timeout_ms: Optional[int] = None


class MonitoredAPIUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    payload: Optional[str] = None
    payload_type: Optional[str] = None
    headers: Optional[dict] = None
    timeout_ms: Optional[int] = None
    is_active: Optional[bool] = None

class MonitoredAPIResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    url: str
    method: str
    payload: Optional[str] = None
    payload_type: Optional[str] = None
    headers: Optional[Dict] = None
    timeout_ms: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True   # 🔥 important for SQLAlchemy
class APILogResponse(BaseModel):
    # APILog.id is BIGSERIAL (integer) in DB
    id: UUID
    api_id: UUID
    tenant_id: UUID
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    response_body: Optional[str] = None
    checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleCreate(BaseModel):
    interval_seconds: int
    # total duration to run the schedule in seconds (optional). If omitted, run indefinitely.
    duration_seconds: Optional[int] = None


class ScheduleResponse(BaseModel):
    id: int
    api_id: UUID
    tenant_id: UUID
    interval_seconds: int
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    # optional end time for the schedule
    end_at: Optional[datetime] = None
    class Config:
        # Pydantic v2
        from_attributes = True
