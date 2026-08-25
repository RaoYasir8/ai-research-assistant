from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_env: str = "development"
    secret_key: str = Field(min_length=32)
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    research_queue: str = "research:runs"
    worker_group: str = "research-workers"
    frontend_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:1.7b"
    ollama_timeout_seconds: int = 180

    searxng_url: str = "http://searxng:8080"
    max_search_results_per_query: int = 5
    max_source_chars: int = 5500
    max_fetch_bytes: int = 1_200_000
    source_fetch_timeout_seconds: int = 12

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
