"""Конфигурация приложения"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Bot settings
    BOT_TOKEN: str
    ADMIN_ID: int
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./gryadka.db"
    
    # Mini App
    MINI_APP_URL: str = "https://your-mini-app-url.com"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # Payment
    PAYMENT_PROVIDER_TOKEN: Optional[str] = None
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "mini_app" / "static" / "uploads"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Создаем экземпляр настроек
settings = Settings()

# Создаем директорию для загрузок, если не существует
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
