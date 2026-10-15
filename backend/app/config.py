from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent

_PLACEHOLDER_MARKERS = (
    "your-key-here",
    "your-service-role-key",
    "your-jwt-secret",
    "your-anon-key",
    "your-project.supabase.co",
    "sk-your-key",
    "changeme",
    "replace-me",
)


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _env_files() -> tuple[str, ...]:
    files: list[str] = []
    for path in (BACKEND_DIR / ".env", REPO_DIR / ".env"):
        if path.is_file():
            files.append(str(path))
    return tuple(files)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 45
    openai_max_tokens: int = 1800

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_anon_key: str | None = None

    counsellor_emails: str = ""
    experiment_treatment_ratio: float = 0.5
    rate_limit_per_minute: int = 30

    @field_validator(
        "openai_api_key",
        "supabase_url",
        "supabase_service_role_key",
        "supabase_jwt_secret",
        "supabase_anon_key",
        mode="before",
    )
    @classmethod
    def drop_placeholders(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value)
        return None if _is_placeholder(text) else text.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def counsellor_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.counsellor_emails.split(",") if e.strip()}

    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    def auth_configured(self) -> bool:
        return bool(self.supabase_jwt_secret) or self.supabase_configured()

    def missing_settings(self) -> list[str]:
        missing: list[str] = []
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.supabase_jwt_secret and not self.supabase_configured():
            missing.append("SUPABASE_JWT_SECRET")
        if not self.counsellor_email_set:
            missing.append("COUNSELLOR_EMAILS")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
