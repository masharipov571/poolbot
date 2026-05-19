import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str = "7294829384:AAH_DummyTokenForDevelopmentUseOnly" # Default fallback for local init
    DATABASE_URL: str = "sqlite+aiosqlite:///./poolbot.db"
    JWT_SECRET: str = "super_secret_poolbot_jwt_key_development_only_123456"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120 # 2 hours session expire
    
    # Primary Admin Telegram ID (must be a valid Telegram User ID)
    ADMIN_TELEGRAM_ID: int = 123456789 # Replace with real admin ID
    
    # Telegram Admin Group ID for Support tickets (Group chat ID like -100xxx)
    ADMIN_GROUP_ID: Optional[int] = None
    
    # Host/Port for FastAPI
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Webhook or Polling mode
    WEBHOOK_MODE: bool = False
    WEBHOOK_URL: Optional[str] = None
    
    # Custom WebApp Domain (e.g. Railway domain like https://poolbot.up.railway.app)
    WEBAPP_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure standard data directory exists for uploads/sqlite
os.makedirs("./data", exist_ok=True)
