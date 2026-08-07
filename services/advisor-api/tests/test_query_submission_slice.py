import uuid

from fastapi.testclient import TestClient

from hive_sight_advisor_api.dependencies import get_db_connection, get_rate_limiter
from hive_sight_advisor_api.guest import GUEST_MEMBERSHIP_ID, GUEST_USER_ID, GUEST_WORKSPACE_ID
from hive_sight_advisor_api.main import app
from hive_sight_advisor_api.rate_limiter import InMemoryRateLimiter


def _seed_guest_workspace(cursor) -> None:
    cursor.execute("INSERT INTO users (id) VALUES (%s)", (GUEST_USER_ID,))
    cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (GUEST_WORKSPACE_ID,))
    cursor.execute(
        """
        INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
        VALUES (%s, %s, %s, 'owner', 'active')
        """,
        (GUEST_MEMBERSHIP_ID, GUEST_USER_ID, GUEST_WORKSPACE_ID),
    )


def test_submit_query_as_a_guest_returns_a_grounded_answer_with_no_auth_header(
    postgres_connection,
) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        jurisdiction_id = uuid.uuid4()
        corpus_document_id = uuid.uuid4()
        passage_id = uuid.uuid4()
        embedding = [0.0] * 1024

        with postgres_connection.cursor() as cursor:
            _seed_guest_workspace(cursor)
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
                    "HBHC",
                    "https://honeybeehealthcoalition.org/varroa/",
                    "CC BY-NC-ND",
                ),
            )
            cursor.execute(
                """
                INSERT INTO passages (id, corpus_document_id, text_content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (passage_id, corpus_document_id, "Treat varroa with oxalic acid.", embedding),
            )
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/queries",
            json={"jurisdiction_id": str(jurisdiction_id), "text": "How do I treat varroa?"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "grounded"
        assert body["citations"] == [
            {
                "passage_id": str(passage_id),
                "document_title": "Varroa Guide",
                "document_source": "HBHC",
                "document_source_url": "https://honeybeehealthcoalition.org/varroa/",
                "document_licence_terms": "CC BY-NC-ND",
                "is_superseded": False,
                "superseded_by_document_title": None,
            }
        ]
        assert "oxalic acid" in body["text"]
    finally:
        app.dependency_overrides.clear()


def test_submit_query_beyond_the_guest_rate_limit_returns_429(postgres_connection) -> None:
    limiter = InMemoryRateLimiter(limit=1, window_seconds=3600)
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    try:
        jurisdiction_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            _seed_guest_workspace(cursor)
            cursor.execute(
                "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
                (jurisdiction_id, "uk", "United Kingdom"),
            )
        postgres_connection.commit()

        client = TestClient(app)
        first = client.post(
            "/queries",
            json={"jurisdiction_id": str(jurisdiction_id), "text": "How do I treat varroa?"},
        )
        assert first.status_code == 200

        second = client.post(
            "/queries",
            json={"jurisdiction_id": str(jurisdiction_id), "text": "How do I treat varroa?"},
        )

        assert second.status_code == 429
        assert second.json()["detail"]["reason"] == "guest_rate_limit_exceeded"
    finally:
        app.dependency_overrides.clear()
