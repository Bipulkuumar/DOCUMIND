import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "DocuMind"
    ENVIRONMENT: str = "development"
    APP_ENV: str = ""
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "default-secret-key-change-in-production-32chars"

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def assemble_environment(cls, v: str, info) -> str:
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def assemble_debug(cls, v: bool, info) -> bool:
        return v

    @model_validator(mode="after")
    def sync_app_env(self) -> "Settings":
        if self.APP_ENV:
            self.ENVIRONMENT = self.APP_ENV
        if self.ENVIRONMENT.lower() == "production":
            self.DEBUG = False
        return self

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    CORS_ORIGIN_REGEX: str = r"https://.*\\.vercel\\.app"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        raise ValueError(v)

    PORT: int = 8000

    # Database
    POSTGRES_USER: str = "documind"
    POSTGRES_PASSWORD: str = "documind_secret"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "documind_db"
    DATABASE_URL: str = "postgresql+asyncpg://documind:documind_secret@localhost:5432/documind_db"

    # Security & JWT
    JWT_SECRET_KEY: str = "documind-jwt-secret-key-replace-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Storage
    STORAGE_DIR: str = "storage/documents"
    MAX_UPLOAD_SIZE_MB: int = 25

    # AI Configuration
    LLM_PROVIDER: str = "openai"  # "openai", "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_BASE_URL: str = "https://api.openai.com/v1"

    EMBEDDING_PROVIDER: str = "local"  # "local", "openai", "mock"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384


settings = Settings()
