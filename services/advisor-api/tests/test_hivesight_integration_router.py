import uuid

from fastapi.testclient import TestClient

from hive_sight_advisor_api.dependencies import get_checkpointer, get_db_connection, get_settings
from hive_sight_advisor_api.main import app
from hive_sight_advisor_api.settings import Settings

SERVICE_KEY = "test-hivesight-service-key"


def _settings() -> Settings:
    return Settings(
        database_url="postgresql://user:pass@localhost:5433/db",
        voyage_api_key="",
        anthropic_api_key="",
        hivesight_service_key=SERVICE_KEY,
        grounded_distance_threshold=0.5,
        partial_distance_threshold=0.8,
    )


def _seed_jurisdiction_with_passage(cursor, jurisdiction_id) -> None:
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = [0.0] * 1024
    cursor.execute(
        "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
        (jurisdiction_id, "uk", "United Kingdom"),
    )
    cursor.execute(
        """
        INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            corpus_document_id,
            jurisdiction_id,
            "Varroa Guide",
            "APHA BeeBase",
            "https://www.nationalbeeunit.com/",
            "Open Government Licence",
        ),
    )
    cursor.execute(
        """
        INSERT INTO passages (id, corpus_document_id, text_content, embedding)
        VALUES (%s, %s, %s, %s)
        """,
        (passage_id, corpus_document_id, "Treat varroa with oxalic acid vaporisation.", embedding),
    )


def _override(postgres_connection, checkpointer) -> None:
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    app.dependency_overrides[get_checkpointer] = lambda: checkpointer


def test_hivesight_requests_a_treatment_plan_and_the_recommendation_is_grounded(
    postgres_connection, checkpointer
) -> None:
    """Scenario: HiveSight requests a treatment plan and the recommendation is grounded."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-42",
                "jurisdiction_id": str(jurisdiction_id),
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "grounded"
        assert len(body["citations"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_a_request_without_a_valid_service_credential_is_rejected(
    postgres_connection, checkpointer
) -> None:
    """Scenario: A request without a valid service credential is rejected."""
    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-42",
                "jurisdiction_id": str(uuid.uuid4()),
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": "wrong-key"},
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_no_relevant_guidance_exists_for_the_requested_hives_situation(
    postgres_connection, checkpointer
) -> None:
    """Scenario: No relevant guidance exists for the requested hive's situation."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-99",
                "jurisdiction_id": str(jurisdiction_id),
                "situational_context": "Should I paint my hive a different colour?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "ungrounded"
        assert body["citations"] == []
    finally:
        app.dependency_overrides.clear()


def test_hivesight_confirms_a_suggested_treatment_was_completed(
    postgres_connection, checkpointer
) -> None:
    """Scenario: HiveSight confirms a suggested treatment was completed."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-7",
                "jurisdiction_id": str(jurisdiction_id),
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        response = client.post(
            "/integrations/hivesight/treatment-plans/completions",
            json={"hive_id": "hivesight-hive-7"},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    finally:
        app.dependency_overrides.clear()
