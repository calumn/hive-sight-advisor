import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    voyage_api_key: str
    anthropic_api_key: str
    dev_user_header: str = "X-Dev-User-Id"
    allowed_origins: list[str] | None = None


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://hive_sight_advisor:hive_sight_advisor@localhost:5433/hive_sight_advisor_dev",
        ),
        voyage_api_key=os.getenv("VOYAGE_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        dev_user_header=os.getenv("ADVISOR_API_DEV_USER_HEADER", "X-Dev-User-Id"),
        allowed_origins=_csv_env(
            "ADVISOR_API_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
    )


def _csv_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]
