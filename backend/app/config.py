from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRIVIA_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./trivia.db"
    media_root: Path = Path("./media")
    seed_on_start: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    worker_interval_seconds: int = 3600

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
