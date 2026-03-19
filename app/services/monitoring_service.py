"""Service layer for monitored APIs and invocation handling."""
from typing import List, Optional
from time import perf_counter
import logging

import httpx
from sqlalchemy.orm import Session

from app.models.monitored import MonitoredAPI, APILog, APISchedule

logger = logging.getLogger(__name__)


class APIService:
    @staticmethod
    def create_api(db: Session, tenant_id: str, data) -> MonitoredAPI:
        api = MonitoredAPI(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            url=data.url,
            method=(data.method or "GET").upper(),
            payload=data.payload,
            payload_type=data.payload_type,
            headers=data.headers,
            timeout_ms=data.timeout_ms,
            is_active=True,
        )
        db.add(api)
        db.commit()
        db.refresh(api)
        return api

    @staticmethod
    def get_api(db: Session, tenant_id: str, api_id: str) -> Optional[MonitoredAPI]:
        return db.query(MonitoredAPI).filter(MonitoredAPI.id == api_id, MonitoredAPI.tenant_id == tenant_id).first()

    @staticmethod
    def list_apis(db: Session, tenant_id: str) -> List[MonitoredAPI]:
        return db.query(MonitoredAPI).filter(MonitoredAPI.tenant_id == tenant_id).all()

    @staticmethod
    def update_api(db: Session, tenant_id: str, api_id: str, data) -> Optional[MonitoredAPI]:
        api = APIService.get_api(db, tenant_id, api_id)
        if not api:
            return None
        update_data = data.dict(exclude_unset=True)
        for k, v in update_data.items():
            setattr(api, k, v)
        db.commit()
        db.refresh(api)
        return api

    @staticmethod
    def delete_api(db: Session, tenant_id: str, api_id: str) -> bool:
        api = APIService.get_api(db, tenant_id, api_id)
        if not api:
            return False

        # Explicitly remove schedules for this API.
        # NOTE: DB FKs are defined with ON DELETE CASCADE, but we do this defensively
        # to match requested behavior across environments.
        db.query(APISchedule).filter(
            APISchedule.api_id == api.id,
            APISchedule.tenant_id == api.tenant_id,
        ).delete(synchronize_session=False)

        db.delete(api)
        db.commit()
        return True

    @staticmethod
    def delete_schedules_for_api(db: Session, tenant_id: str, api_id: str) -> int:
        """Delete all schedules for a given API within a tenant.

        Returns the number of deleted schedule rows.
        """
        api = APIService.get_api(db, tenant_id, api_id)
        if not api:
            return 0

        deleted = db.query(APISchedule).filter(
            APISchedule.api_id == api.id,
            APISchedule.tenant_id == api.tenant_id,
        ).delete(synchronize_session=False)
        db.commit()
        return int(deleted or 0)

    @staticmethod
    def delete_schedule_by_id(db: Session, tenant_id: str, schedule_id: int) -> bool:
        """Delete a schedule row by its id within a tenant."""
        sched = db.query(APISchedule).filter(
            APISchedule.id == schedule_id,
            APISchedule.tenant_id == tenant_id,
        ).first()
        if not sched:
            return False
        db.delete(sched)
        db.commit()
        return True


class MonitoringService:
    @staticmethod
    async def invoke_and_log(db: Session, api: MonitoredAPI) -> APILog:
        timeout = 10.0
        if api.timeout_ms:
            try:
                timeout = float(api.timeout_ms) / 1000.0
            except Exception:
                timeout = 10.0

        method = (api.method or "GET").upper()
        headers = api.headers or {}

        # Normalize headers if stored as string
        if isinstance(headers, str):
            try:
                import json as _json
                headers = _json.loads(headers)
            except Exception:
                headers = {}

        data = None
        json = None

        # Methods that allow or require a body
        body_methods = {"POST", "PUT", "PATCH"}

        # If method does not support body, ignore any stored payload
        if method not in body_methods:
            data = None
            json = None
        else:
            # For body methods, payload_type is required when payload is provided
            if api.payload and not api.payload_type:
                # create a failure log entry describing the missing payload_type
                log = APILog(
                    api_id=api.id,
                    tenant_id=api.tenant_id,
                    status_code=None,
                    response_time_ms=0,
                    success=False,
                    error_message="payload_type is required for HTTP method %s" % method,
                    response_body=None,
                )
                db.add(log)
                db.commit()
                db.refresh(log)
                return log

            if api.payload:
                if api.payload_type and api.payload_type.lower() == "json":
                    try:
                        import json as _json
                        json = _json.loads(api.payload)
                    except Exception as exc:
                        # JSON parsing failed — record failure log
                        log = APILog(
                            api_id=api.id,
                            tenant_id=api.tenant_id,
                            status_code=None,
                            response_time_ms=0,
                            success=False,
                            error_message="failed to parse payload as json: %s" % str(exc),
                            response_body=None,
                        )
                        db.add(log)
                        db.commit()
                        db.refresh(log)
                        return log
                else:
                    data = api.payload

        async with httpx.AsyncClient(timeout=timeout) as client:
            start = perf_counter()
            try:
                # Build kwargs dynamically to avoid sending None for data/json
                req_kwargs = {"headers": headers}
                if json is not None:
                    req_kwargs["json"] = json
                elif data is not None:
                    req_kwargs["data"] = data

                resp = await client.request(method, api.url, **req_kwargs)
                elapsed = int((perf_counter() - start) * 1000)
                log = APILog(
                    api_id=api.id,
                    tenant_id=api.tenant_id,
                    status_code=resp.status_code,
                    response_time_ms=elapsed,
                    success=200 <= resp.status_code < 300,
                    error_message=None,
                    response_body=resp.text[:10000],
                )
            except Exception as exc:
                elapsed = int((perf_counter() - start) * 1000)
                logger.exception("invoke failed for api %s: %s", api.id, exc)
                log = APILog(
                    api_id=api.id,
                    tenant_id=api.tenant_id,
                    status_code=None,
                    response_time_ms=elapsed,
                    success=False,
                    error_message=str(exc),
                    response_body=None,
                )

        db.add(log)
        db.commit()
        db.refresh(log)
        return log


api_service = APIService()
monitoring_service = MonitoringService()
