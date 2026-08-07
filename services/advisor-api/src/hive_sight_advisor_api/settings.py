import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    voyage_api_key: str
    anthropic_api_key: str
    dev_user_header: str = "X-Dev-User-Id"
    allowed_origins: list[str] | None = None
    grounded_distance_threshold: float = 0.35
    partial_distance_threshold: float = 0.55
    hivesight_service_key: str = ""
    guest_rate_limit: int = 10
    guest_rate_limit_window_seconds: float = 3600.0


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
            "http://localhost:5183,http://127.0.0.1:5183",
        ),
        grounded_distance_threshold=float(
            os.getenv("ADVISOR_API_GROUNDED_DISTANCE_THRESHOLD", "0.35")
        ),
        partial_distance_threshold=float(
            os.getenv("ADVISOR_API_PARTIAL_DISTANCE_THRESHOLD", "0.55")
        ),
        hivesight_service_key=os.getenv("ADVISOR_API_HIVESIGHT_SERVICE_KEY", ""),
        guest_rate_limit=int(os.getenv("ADVISOR_API_GUEST_RATE_LIMIT", "10")),
        guest_rate_limit_window_seconds=float(
            os.getenv("ADVISOR_API_GUEST_RATE_LIMIT_WINDOW_SECONDS", "3600")
        ),
    )


def _csv_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]
