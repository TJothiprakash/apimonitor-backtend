"""Routes to register, update, delete, test, and schedule APIs for a tenant."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.base import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.monitoring import (
    MonitoredAPICreate,
    MonitoredAPIResponse,
    MonitoredAPIUpdate,
    APILogResponse,
    ScheduleCreate,
    ScheduleResponse,
)
from app.services.monitoring_service import api_service, monitoring_service
from app.models.monitored import APISchedule, APILog
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/monitor/apis", response_model=MonitoredAPIResponse, status_code=status.HTTP_201_CREATED)
async def register_api(payload: MonitoredAPICreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    # Validate payload rules: for body methods payload_type required, for non-body methods payload must be empty
    method = (payload.method or "GET").upper()
    body_methods = {"POST", "PUT", "PATCH"}
    allowed_payload_types = {"json", "form", "raw"}

    if payload.payload:
        if method not in body_methods:
            raise HTTPException(status_code=400, detail=f"HTTP method {method} must not include a payload")
        if not payload.payload_type:
            raise HTTPException(status_code=400, detail="payload_type is required when payload is provided")
        if payload.payload_type.lower() not in allowed_payload_types:
            raise HTTPException(status_code=400, detail=f"unsupported payload_type '{payload.payload_type}'")

    api = api_service.create_api(db, tenant_id, payload)
    return api


@router.get("/monitor/apis", response_model=List[MonitoredAPIResponse])
async def list_apis(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    apis = api_service.list_apis(db, tenant_id)
    return apis


@router.get("/monitor/apis/{api_id}", response_model=MonitoredAPIResponse)
async def get_api(api_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    api = api_service.get_api(db, tenant_id, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    return api


@router.put("/monitor/apis/{api_id}", response_model=MonitoredAPIResponse)
async def update_api(api_id: str, payload: MonitoredAPIUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    # Validate update rules similar to create
    if payload.method:
        method = payload.method.upper()
    else:
        # if method not provided, fetch existing API to know method
        existing = api_service.get_api(db, tenant_id, api_id)
        if not existing:
            raise HTTPException(status_code=404, detail="API not found")
        method = existing.method or "GET"

    method = method.upper()
    body_methods = {"POST", "PUT", "PATCH"}
    allowed_payload_types = {"json", "form", "raw"}

    if getattr(payload, "payload", None):
        if method not in body_methods:
            raise HTTPException(status_code=400, detail=f"HTTP method {method} must not include a payload")
        if not getattr(payload, "payload_type", None):
            raise HTTPException(status_code=400, detail="payload_type is required when payload is provided")
        if payload.payload_type and payload.payload_type.lower() not in allowed_payload_types:
            raise HTTPException(status_code=400, detail=f"unsupported payload_type '{payload.payload_type}'")

    api = api_service.update_api(db, tenant_id, api_id, payload)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    return api


@router.delete("/monitor/apis/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api(api_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    ok = api_service.delete_api(db, tenant_id, api_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API not found")
    return None


@router.delete("/monitor/apis/{api_id}/schedules", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_schedules(api_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Delete scheduled runs for a specific API (does not delete the API itself)."""
    tenant_id = str(current_user.tenant_id)
    deleted = api_service.delete_schedules_for_api(db, tenant_id, api_id)
    if deleted == 0:
        # Could be either: API not found, or API exists but has no schedules.
        # Keep behavior strict (404) only if the API itself doesn't exist.
        api = api_service.get_api(db, tenant_id, api_id)
        if not api:
            raise HTTPException(status_code=404, detail="API not found")
    return None


@router.delete("/monitor/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Delete a single schedule entry by schedule id."""
    tenant_id = str(current_user.tenant_id)
    ok = api_service.delete_schedule_by_id(db, tenant_id, schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return None


@router.post("/monitor/apis/{api_id}/test", response_model=APILogResponse)
async def test_api(api_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    api = api_service.get_api(db, tenant_id, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    log = await monitoring_service.invoke_and_log(db, api)
    return log


@router.post("/monitor/apis/{api_id}/schedule", response_model=ScheduleResponse)
async def schedule_api(api_id: str, payload: ScheduleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    api = api_service.get_api(db, tenant_id, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")

    # validate interval range
    if payload.interval_seconds < 30 or payload.interval_seconds > 1800:
        raise HTTPException(status_code=400, detail="interval_seconds must be between 30 and 1800")

    now = datetime.utcnow()
    next_run = now + timedelta(seconds=payload.interval_seconds)

    # optional duration handling
    end_at = None
    if getattr(payload, "duration_seconds", None):
        # enforce a reasonable maximum (e.g., 7 days)
        max_duration = 7 * 24 * 3600
        if payload.duration_seconds < payload.interval_seconds or payload.duration_seconds > max_duration:
            raise HTTPException(status_code=400, detail=f"duration_seconds must be >= interval_seconds and <= {max_duration}")
        end_at = now + timedelta(seconds=payload.duration_seconds)

    schedule = APISchedule(
        api_id=api.id,
        tenant_id=api.tenant_id,
        interval_seconds=payload.interval_seconds,
        enabled=True,
        next_run=next_run,
        end_at=end_at,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


@router.get("/monitor/apis/{api_id}/logs", response_model=List[APILogResponse])
async def get_logs(api_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant_id = str(current_user.tenant_id)
    api = api_service.get_api(db, tenant_id, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    logs = db.query(APILog).filter(APILog.api_id == api_id, APILog.tenant_id == tenant_id).order_by(APILog.checked_at.desc()).all()
    return logs
