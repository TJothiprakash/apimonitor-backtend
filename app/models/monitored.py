from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.base import Base


class MonitoredAPI(Base):
    __tablename__ = "monitored_apis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    method = Column(String(10), nullable=False, default="GET")
    payload = Column(Text, nullable=True)
    payload_type = Column(String(50), nullable=True)
    headers = Column(JSON, nullable=True)
    timeout_ms = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(BigInteger, primary_key=True)
    api_id = Column(UUID(as_uuid=True), ForeignKey("monitored_apis.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)

    checked_at = Column(DateTime(timezone=True), server_default=func.now())


class APISchedule(Base):
    __tablename__ = "api_schedules"

    id = Column(BigInteger, primary_key=True)
    api_id = Column(UUID(as_uuid=True), ForeignKey("monitored_apis.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    interval_seconds = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
