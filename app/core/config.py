from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_rate_limit: str = Field(default="100/minute", alias="API_RATE_LIMIT")
    
    # Model paths
    model_path: str = Field(
        default="./models/model.joblib", alias="MODEL_PATH"
    )
    preprocessor_path: str = Field(
        default="./models/preprocessor.joblib", alias="PREPROCESSOR_PATH"
    )
    
    # Training schedule (Saturday at 12:00 PM)
    retrain_day: int = Field(default=5, alias="RETRAIN_DAY")  # 5 = Saturday
    retrain_hour: int = Field(default=12, alias="RETRAIN_HOUR")
    retrain_minute: int = Field(default=0, alias="RETRAIN_MINUTE")

    @field_validator("retrain_day")
    @classmethod
    def validate_day(cls, v: int) -> int:
        if not 0 <= v <= 6:
            raise ValueError("retrain_day must be between 0 (Monday) and 6 (Sunday)")
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()