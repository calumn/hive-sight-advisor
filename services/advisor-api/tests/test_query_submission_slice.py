import uuid

from fastapi.testclient import TestClient

from hive_sight_advisor_api.dependencies import get_db_connection
from hive_sight_advisor_api.main import app


def test_submit_query_with_valid_membership_returns_grounded_answer(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        jurisdiction_id = uuid.uuid4()
        corpus_document_id = uuid.uuid4()
        passage_id = uuid.uuid4()
        embedding = [0.0] * 1024

        with postgres_connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
            cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
            cursor.execute(
                """
                INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                VALUES (%s, %s, %s, 'owner', 'active')
                """,
                (uuid.uuid4(), user_id, workspace_id),
            )
            cursor.execute(
                "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
                (jurisdiction_id, "uk", "United Kingdom"),
            )
            cursor.execute(
                """
                INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (corpus_document_id, jurisdiction_id, "Varroa Guide", "HBHC", "CC BY-NC-ND"),
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
            json={
                "workspace_id": str(workspace_id),
                "jurisdiction_id": str(jurisdiction_id),
                "text": "How do I treat varroa?",
            },
            headers={"x-dev-user-id": str(user_id)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["grounding_status"] == "grounded"
        assert body["citations"] == [{"passage_id": str(passage_id)}]
        assert "oxalic acid" in body["text"]
    finally:
        app.dependency_overrides.clear()


def test_submit_query_without_membership_is_rejected(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/queries",
            json={
                "workspace_id": str(workspace_id),
                "jurisdiction_id": str(uuid.uuid4()),
                "text": "How do I treat varroa?",
            },
            headers={"x-dev-user-id": str(uuid.uuid4())},
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
