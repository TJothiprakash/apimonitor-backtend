"""
FastAPI API Monitoring Backend with JWT Authentication
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.core.config import settings
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


app = FastAPI(
    title="API Monitoring Service",
    description="Professional API Monitoring Service with JWT Authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
from app.routers import monitor as monitor_router
app.include_router(monitor_router.router, prefix="/api/v1", tags=["Monitoring"])

@app.get("/")
async def root():
    return {"message": "API Monitoring Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "API Monitoring Backend"}


# scheduler and monitoring router removed; only auth routes are included


import asyncio
from datetime import datetime, timedelta
from app.database.base import SessionLocal
from app.services.monitoring_service import monitoring_service, api_service
from app.models.monitored import APISchedule


async def scheduler_loop():
    """Background scheduler loop: finds due schedules, invokes APIs, and records logs."""
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc) 
                schedules = db.query(APISchedule).filter(APISchedule.enabled == True).all()
                for sched in schedules:
                    # skip if next_run is set and still in future
                    if sched.next_run and sched.next_run > now:
                        continue

                    # if schedule expired, disable it
                    if sched.end_at and now > sched.end_at:
                        sched.enabled = False
                        sched.next_run = None
                        db.add(sched)
                        db.commit()
                        continue

                    # fetch API and invoke
                    api = api_service.get_api(db, str(sched.tenant_id), str(sched.api_id))
                    if not api:
                        # API missing -- disable schedule
                        sched.enabled = False
                        sched.next_run = None
                        db.add(sched)
                        db.commit()
                        continue

                    try:
                        await monitoring_service.invoke_and_log(db, api)
                    except Exception:
                        # invocation errors are already logged inside service
                        pass

                    # update last_run and compute next_run
                    sched.last_run = now
                    next_run = now + timedelta(seconds=sched.interval_seconds)
                    if sched.end_at and next_run > sched.end_at:
                        sched.enabled = False
                        sched.next_run = None
                    else:
                        sched.next_run = next_run

                    db.add(sched)
                    db.commit()
            finally:
                db.close()
        except Exception:
            logging.exception("scheduler loop error")

        await asyncio.sleep(1)


@app.on_event("startup")
async def start_scheduler():
    # start the background scheduler loop
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop())
