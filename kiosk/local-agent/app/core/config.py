from functools import lru_cache
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME")
    debug: bool = os.getenv("DEBUG") == "true"

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 9001))

    temp_dir: str = os.getenv("TEMP_DIR")
    database_path: str = os.getenv("DATABASE_PATH")

    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB"))
    session_ttl_minutes: int = int(os.getenv("SESSION_TTL_MINUTES"))

    local_public_base_url: str = os.getenv("LOCAL_PUBLIC_BASE_URL")

    hotspot_mode: str = os.getenv("HOTSPOT_MODE")
    hotspot_ssid: str = os.getenv("HOTSPOT_SSID")
    hotspot_password: str = os.getenv("HOTSPOT_PASSWORD")

    frontend_origin: str = os.getenv("FRONTEND_ORIGIN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def temp_path(self) -> Path:
        return Path(self.temp_dir)

    @property
    def database_file(self) -> Path:
        return Path(self.database_path)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()