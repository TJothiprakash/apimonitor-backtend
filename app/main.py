"""
FastAPI API Monitoring Backend with JWT Authentication
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.core.config import settings
import logging

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

@app.get("/")
async def root():
    return {"message": "API Monitoring Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "API Monitoring Backend"}
