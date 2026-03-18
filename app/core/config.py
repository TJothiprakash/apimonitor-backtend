"""
Configuration settings for the API Monitoring application
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import EmailStr


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "API Monitoring Service"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # Security settings
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database settings (use a cloud Postgres by default; override via .env DATABASE_URL)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/apimonitor"
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: EmailStr = "noreply@apimonitor.com"
    EMAILS_FROM_NAME: str = "API Monitor"
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
