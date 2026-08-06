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


def _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id, *, real_embedding=False) -> None:
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


def _override(postgres_connection, checkpointer) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    app.dependency_overrides[get_checkpointer] = lambda: checkpointer


def test_a_treatment_plan_request_succeeds_with_jurisdiction_code_and_carries_audit_fields(
    postgres_connection, checkpointer
) -> None:
    """Scenario: A treatment plan request succeeds with a jurisdiction code and carries audit fields."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-1",
                "jurisdiction_code": "uk",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "grounded"
        assert body["contract_version"] == "treatment_plan_v1"
        assert uuid.UUID(body["answer_id"])
    finally:
        app.dependency_overrides.clear()


def test_a_request_with_an_unknown_jurisdiction_code_is_rejected(
    postgres_connection, checkpointer
) -> None:
    """Scenario: A request with an unknown jurisdiction code is rejected."""
    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        response = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-2",
                "jurisdiction_code": "de",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 422

        with postgres_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM proposed_treatments WHERE hive_id = %s", ("hivesight-hive-2",)
            )
            (count,) = cursor.fetchone()
        assert count == 0
    finally:
        app.dependency_overrides.clear()


def test_repeating_a_request_while_a_suggestion_is_still_pending_returns_the_same_suggestion(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Repeating a request while a suggestion is still pending returns the same suggestion."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        payload = {
            "hive_id": "hivesight-hive-3",
            "jurisdiction_code": "uk",
            "situational_context": "Mite count is high, what treatment should I use?",
        }
        first = client.post(
            "/integrations/hivesight/treatment-plans",
            json=payload,
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        second = client.post(
            "/integrations/hivesight/treatment-plans",
            json=payload,
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert second.status_code == 200
        assert second.json()["answer_id"] == first.json()["answer_id"]

        with postgres_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM proposed_treatments WHERE hive_id = %s", ("hivesight-hive-3",)
            )
            (count,) = cursor.fetchone()
        assert count == 1
    finally:
        app.dependency_overrides.clear()


def test_requesting_again_after_a_suggestion_was_completed_starts_a_fresh_episode(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Requesting again after a suggestion was completed starts a fresh episode."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        payload = {
            "hive_id": "hivesight-hive-4",
            "jurisdiction_code": "uk",
            "situational_context": "Mite count is high, what treatment should I use?",
        }
        first = client.post(
            "/integrations/hivesight/treatment-plans",
            json=payload,
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        client.post(
            "/integrations/hivesight/treatment-plans/completions",
            json={"hive_id": "hivesight-hive-4"},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        second = client.post(
            "/integrations/hivesight/treatment-plans",
            json=payload,
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert second.status_code == 200
        assert second.json()["answer_id"] != first.json()["answer_id"]
    finally:
        app.dependency_overrides.clear()


def test_confirming_a_suggestion_includes_the_answer_id_for_audit_correlation(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Confirming a suggestion includes the answer id for audit correlation."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        requested = client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-5",
                "jurisdiction_code": "uk",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        response = client.post(
            "/integrations/hivesight/treatment-plans/completions",
            json={"hive_id": "hivesight-hive-5"},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["contract_version"] == "treatment_plan_v1"
        assert body["answer_id"] == requested.json()["answer_id"]
    finally:
        app.dependency_overrides.clear()


def test_rejecting_a_suggestion_includes_the_contract_version_and_answer_id(
    postgres_connection, checkpointer
) -> None:
    """Scenario: Rejecting a suggestion includes the contract version and answer id."""
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_uk_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    _override(postgres_connection, checkpointer)
    try:
        client = TestClient(app)
        client.post(
            "/integrations/hivesight/treatment-plans",
            json={
                "hive_id": "hivesight-hive-6",
                "jurisdiction_code": "uk",
                "situational_context": "Mite count is high, what treatment should I use?",
            },
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )
        response = client.post(
            "/integrations/hivesight/treatment-plans/rejections",
            json={"hive_id": "hivesight-hive-6", "reason": "Conflicts with an active honey flow."},
            headers={"x-hivesight-service-key": SERVICE_KEY},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["contract_version"] == "treatment_plan_v1"
        assert uuid.UUID(body["answer_id"])
    finally:
        app.dependency_overrides.clear()
