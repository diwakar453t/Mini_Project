"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ChargeMitra"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Database
    DATABASE_URL: str = "postgresql://chargemitra:chargemitra123@localhost:5432/chargemitra"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File Storage
    UPLOAD_PATH: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp", "pdf"]
    
    # AWS S3 (Production)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    AWS_S3_ENDPOINT_URL: Optional[str] = None
    
    # Payment - Razorpay (Primary)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    
    # Payment - Stripe (Fallback)
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Platform Settings
    PLATFORM_COMMISSION_RATE: float = 15.0
    
    # Google Maps
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    GOOGLE_GEOCODING_API_KEY: Optional[str] = None
    
    # Email - SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@chargemitra.com"
    SENDGRID_FROM_NAME: str = "ChargeMitra"
    
    # SMS - Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Push Notifications
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_SUBJECT: str = "mailto:admin@chargemitra.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    # Session
    SESSION_EXPIRE_SECONDS: int = 3600
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 5
    OTP_LENGTH: int = 6
    
    # Booking Settings
    BOOKING_BUFFER_MINUTES: int = 15
    MAX_BOOKING_DURATION_HOURS: int = 24
    BOOKING_CANCELLATION_WINDOW_HOURS: int = 2
    
    # Host Settings
    HOST_AUTO_ACCEPT_DEFAULT: bool = False
    HOST_KYC_REQUIRED: bool = True
    
    # WebSocket
    WS_CONNECTION_TIMEOUT: int = 300
    
    # Telemetry
    TELEMETRY_UPDATE_INTERVAL: int = 5
    SIMULATE_TELEMETRY: bool = True
    
    # Admin
    ADMIN_EMAIL: str = "admin@chargemitra.com"
    ADMIN_PASSWORD: str = "admin123"
    
    # Test Accounts
    TEST_HOST_EMAIL: str = "host@example.com"
    TEST_HOST_PASSWORD: str = "host123"
    TEST_RENTER_EMAIL: str = "renter@example.com"
    TEST_RENTER_PASSWORD: str = "renter123"
    
    # Payout Settings
    PAYOUT_MINIMUM_AMOUNT: float = 500.0
    PAYOUT_PROCESSING_DAYS: int = 7
    
    # Dispute Settings
    DISPUTE_AUTO_RESOLVE_DAYS: int = 30
    
    # Analytics
    ENABLE_ANALYTICS: bool = True
    ANALYTICS_RETENTION_DAYS: int = 365
    
    # Dummy Payments (Development only)
    USE_DUMMY_PAYMENTS: bool = False

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("ALLOWED_EXTENSIONS", pre=True)
    def assemble_extensions(cls, v):
        if isinstance(v, str):
            return [i.strip().lower() for i in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql://").replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()