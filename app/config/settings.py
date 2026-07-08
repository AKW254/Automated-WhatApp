import json
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
  # ============= APP SETTINGS =============
    app_name: str = "AI Whatsapp Bot"
    app_version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    debug: bool = True  # Enable debug mode for development
    # Logging
    LOG_LEVEL: str = "INFO"
     # ============= SECURITY =============
    jwt_secret_key: str  # REQUIRED - must be set via .env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # CORS Settings
    cors_origins: List[str] = ["*"]  # Allow all origins by default
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # ============= DATABASE =============
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str
    db_echo: bool = False  # SQL logging

    # ============= AI API KEYS =============
 
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model_name: str 
    openrouter_embedding_model_name: str | None = None
    #Celery 
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_always_eager: bool | None = None
    celery_broker_connection_timeout: int = 5
    celery_broker_connection_max_retries: int = 1
    celery_timezone:str
    
    #Whatsapp API
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str | None = None
   
   
   #Load settings from .env file and validate them
    model_config = SettingsConfigDict(
      env_file=ENV_FILE, 
      extra="ignore",
      case_sensitive=False,)
    @field_validator("debug", mode="before")
    @classmethod
    def _parse_debug_value(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
                return False
        return value

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return list"""
        if isinstance(self.cors_origins, str):
            raw_value = self.cors_origins.strip()

            if raw_value.startswith("[") and raw_value.endswith("]"):
                try:
                    parsed = json.loads(raw_value)
                    if isinstance(parsed, list):
                        return [
                            str(origin).strip()
                            for origin in parsed
                            if str(origin).strip()
                        ]
                except json.JSONDecodeError:
                    pass

            return [
                origin.strip().strip('"').strip("'")
                for origin in raw_value.split(",")
                if origin.strip()
            ]
        return self.cors_origins
settings = Settings()  # Load settings from .env file and validate them
