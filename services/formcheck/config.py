from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://formcheck:formcheck@localhost:5432/formcheck"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "http://localhost:9000"
    minio_public_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "formcheck"
    minio_secret_key: str = "formchecksecret"
    minio_bucket: str = "formcheck"
    minio_region: str = "us-east-1"

    api_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    capability_token_pepper: str = "local-dev-pepper-change-me"
    retention_hours: int = 24
    pipeline_version: str = "2026.10.0"
    fake_worker_stage_ms: int = 400
    max_upload_bytes: int = 100 * 1024 * 1024
    upload_url_expires_seconds: int = 900
    # Ratified contract schema_version is "1" (ADR 0001).
    schema_version: str = "1"
    # Temporary: project ratified results to interim frontend shape on GET /result.
    # Person 1 should remap apps/web then set FORMCHECK_INTERIM_RESULT_SHIM=0.
    interim_result_shim: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
