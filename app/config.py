from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения через переменные окружения"""
    
    # RetailCRM
    retailcrm_api_url: str = Field(..., env="RETAILCRM_API_URL")
    retailcrm_api_key: str = Field(..., env="RETAILCRM_API_KEY")
    
    # Supabase
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Telegram
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")
    
    # FastAPI
    fastapi_env: str = Field(default="development", env="FASTAPI_ENV")
    fastapi_port: int = Field(default=8000, env="FASTAPI_PORT")
    cors_origins: str = Field(default="http://localhost:8000,http://localhost:3000", env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
