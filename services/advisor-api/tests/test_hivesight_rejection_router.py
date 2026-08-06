import uuid

from fastapi.testclient import TestClient

from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.dependencies import get_checkpointer, get_db_connection, get_settings
from hive_sight_advisor_api.main import app
from hive_sight_advisor_api.settings import Settings

SERVICE_KEY = "test-hivesight-service-key"


def _settings(**overrides) -> Settings:
    defaults = {
        "database_url": "postgresql://user:pass@localhost:5433/db",
        "voyage_api_key": "",
        "anthropic_api_key": "",
        "hivesight_service_key": SERVICE_KEY,
        "grounded_distance_threshold": 0.5,
        "partial_distance_threshold": 0.8,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _seed_jurisdiction_with_passage(cursor, jurisdiction_id, *, real_embedding=False) -> None:
    passage_text = "Treat varroa with oxalic acid vaporisation."
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = StubEmbeddingProvider().embed(passage_text) if real_embedding else [0.0] * 1024
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
        (passage_id, corpus_document_id, passage_text, embedding),
    )


def _override(postgres_connection, checkpointer, settings=None) -> None:
    resolved_settings = settings or _settings()
    app.dependency_overrides[get_settings] = lambda: resolved_settings
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    app.dependency_overrides[get_checkpointer] = lambda: checkpointer


def test_hivesight_rejects_a_suggested_treatment_and_receives_a_revised_recommendation(
    postgres_connection, checkpointer
) -> None:
    """Scenario: HiveSight rejects a suggested treatment and receives a revised recommendation."""
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
                "hive_id": "hivesight-hive-1",
                "jurisdiction_code": "uk",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        response = client.post(
            "/integrations/hivesight/treatment-plans/rejections",
            json={"hive_id": "hivesight-hive-1", "reason": "Conflicts with an active honey flow."},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "grounded"
        assert body["revision_exhausted"] is False
    finally:
        app.dependency_overrides.clear()


def test_repeated_rejection_eventually_exhausts_the_revision_limit(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Repeated rejection eventually exhausts the revision limit."""
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
                "hive_id": "hivesight-hive-2",
                "jurisdiction_code": "uk",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        for i in range(3):
            client.post(
                "/integrations/hivesight/treatment-plans/rejections",
                json={"hive_id": "hivesight-hive-2", "reason": f"Reason {i}"},
                headers={"x-hivesight-service-key": SERVICE_KEY},
            )

        response = client.post(
            "/integrations/hivesight/treatment-plans/rejections",
            json={"hive_id": "hivesight-hive-2", "reason": "One rejection too many"},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        assert response.json()["revision_exhausted"] is True
    finally:
        app.dependency_overrides.clear()


def test_rejecting_when_nothing_is_awaiting_completion_is_rejected(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Rejecting when nothing is awaiting completion is rejected."""
    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans/rejections",
            json={"hive_id": "hivesight-hive-does-not-exist", "reason": "No reason"},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_a_revised_recommendation_itself_has_no_grounded_answer(
    postgres_connection, checkpointer
) -> None:
    """Scenario: A revised recommendation itself has no grounded answer."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id, real_embedding=True)
    postgres_connection.commit()

    tight_settings = _settings(grounded_distance_threshold=0.35, partial_distance_threshold=0.55)
    _override(postgres_connection, checkpointer, settings=tight_settings)
    try:
        client = TestClient(app)
        client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-3",
                "jurisdiction_code": "uk",
                "situational_context": "How do I treat varroa with oxalic acid vaporisation?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        response = client.post(
            "/integrations/hivesight/treatment-plans/rejections",
            json={
                "hive_id": "hivesight-hive-3",
                "reason": (
                    "giraffe astronomy bicycle continent orchestra volcano telephone "
                    "galaxy umbrella xylophone quokka marmalade lighthouse saxophone tundra"
                ),
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "ungrounded"
        assert body["revision_exhausted"] is False
    finally:
        app.dependency_overrides.clear()
