from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ARAIAP_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Araiap API"
    environment: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://araiap:araiap@localhost:5432/araiap"

    storage_backend: str = "local"
    public_base_url: str = "http://127.0.0.1:8000"
    local_storage_dir: str = "data"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_public_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_bucket: str = "araiap-floor-plans"
    s3_region: str = "us-east-1"
    signed_url_expires_seconds: int = 3600
    max_floor_plan_bytes: int = 15 * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
