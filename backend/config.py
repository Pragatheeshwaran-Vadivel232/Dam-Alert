import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://damuser:Pragaruthee1234@localhost:5432/damalert")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MSG91_AUTH_KEY: str = os.getenv("MSG91_AUTH_KEY", "")
    SMS_SENDER_ID: str = os.getenv("SMS_SENDER_ID", "KLDAMT")
    TEMPLATE_DAILY_DIGEST: str = os.getenv("TEMPLATE_DAILY_DIGEST", "fill_this_later")
    TEMPLATE_CAUTION: str = os.getenv("TEMPLATE_CAUTION", "fill_this_later")
    TEMPLATE_HIGH: str = os.getenv("TEMPLATE_HIGH", "fill_this_later")
    TEMPLATE_CRITICAL: str = os.getenv("TEMPLATE_CRITICAL", "fill_this_later")
    TEMPLATE_RELEASE: str = os.getenv("TEMPLATE_RELEASE", "fill_this_later")
    TEMPLATE_LEVEL: str = os.getenv("TEMPLATE_LEVEL", "fill_this_later")
    TEMPLATE_LOW: str = os.getenv("TEMPLATE_LOW", "fill_this_later")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "damalert2026secretkeyforjwt")
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "8"))
    ADMIN_PHONE: str = os.getenv("ADMIN_PHONE", "+919400000000")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()
