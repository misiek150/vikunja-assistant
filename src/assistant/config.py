from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogMode(StrEnum):
    CONSOLE = "console"
    SEQ = "seq"


class Settings(BaseSettings):
    """Application configuration, driven by environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    log_mode: LogMode = LogMode.CONSOLE
    log_level: str = "INFO"
    seq_url: str | None = None
    seq_api_key: SecretStr | None = None

    mock_mode: bool = False
    mock_responses_dir: Path | None = None

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"
    prompt_path: Path | None = None

    vikunja_base_url: str = "http://localhost:3456"
    vikunja_api_token: SecretStr | None = None
    vikunja_project_id: int = Field(default=1, ge=1)

    screenshots_dir: Path = Path("./data/screenshots")
    processed_dir: Path | None = None

    @model_validator(mode="after")
    def _check_seq(self) -> Self:
        if self.log_mode is LogMode.SEQ and not self.seq_url:
            raise ValueError("SEQ_URL is required when LOG_MODE=seq")
        return self

    @property
    def effective_processed_dir(self) -> Path:
        return self.processed_dir or self.screenshots_dir / "processed"
