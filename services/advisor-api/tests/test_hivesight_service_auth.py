import pytest
from fastapi import HTTPException

from hive_sight_advisor_api.dependencies import get_hivesight_service_credential
from hive_sight_advisor_api.settings import Settings


def _settings(hivesight_service_key: str = "test-service-key") -> Settings:
    return Settings(
        database_url="postgresql://user:pass@localhost:5433/db",
        voyage_api_key="",
        anthropic_api_key="",
        hivesight_service_key=hivesight_service_key,
    )


def test_valid_service_credential_is_accepted() -> None:
    get_hivesight_service_credential(_settings(), x_hivesight_service_key="test-service-key")


def test_missing_service_credential_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_hivesight_service_credential(_settings(), x_hivesight_service_key=None)

    assert exc_info.value.status_code == 401


def test_incorrect_service_credential_is_rejected() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_hivesight_service_credential(_settings(), x_hivesight_service_key="wrong-key")

    assert exc_info.value.status_code == 401


def test_credential_is_rejected_when_no_key_is_configured() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_hivesight_service_credential(_settings(hivesight_service_key=""), x_hivesight_service_key="")

    assert exc_info.value.status_code == 401
