import uuid

from fastapi.testclient import TestClient

from hive_sight_advisor_api.dependencies import get_db_connection
from hive_sight_advisor_api.main import app


def _seed_workspace_with_answer(cursor, *, user_id, workspace_id):
    query_id = uuid.uuid4()
    answer_id = uuid.uuid4()
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
        "INSERT INTO queries (id, workspace_id, text) VALUES (%s, %s, %s)",
        (query_id, workspace_id, "How do I treat varroa?"),
    )
    cursor.execute(
        "INSERT INTO answers (id, query_id, text, grounding_status) VALUES (%s, %s, %s, %s)",
        (answer_id, query_id, "Some answer text.", "grounded"),
    )
    return answer_id


def test_submit_correction_with_valid_membership_persists_it(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            answer_id = _seed_workspace_with_answer(cursor, user_id=user_id, workspace_id=workspace_id)
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/corrections",
            json={
                "workspace_id": str(workspace_id),
                "answer_id": str(answer_id),
                "notes": "This cites the wrong jurisdiction's guidance."
            },
            headers={"x-dev-user-id": str(user_id)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["answer_id"] == str(answer_id)
        assert body["status"] == "trusted"

        with postgres_connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM corrections WHERE answer_id = %s", (answer_id,))
            (count,) = cursor.fetchone()
        assert count == 1
    finally:
        app.dependency_overrides.clear()


def test_submit_correction_twice_for_the_same_answer_both_succeed(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            answer_id = _seed_workspace_with_answer(cursor, user_id=user_id, workspace_id=workspace_id)
        postgres_connection.commit()

        client = TestClient(app)
        for notes in ("First issue.", "Second issue."):
            response = client.post(
                "/corrections",
                json={
                    "workspace_id": str(workspace_id),
                    "answer_id": str(answer_id),
                    "notes": notes
                },
                headers={"x-dev-user-id": str(user_id)},
            )
            assert response.status_code == 200

        with postgres_connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM corrections WHERE answer_id = %s", (answer_id,))
            (count,) = cursor.fetchone()
        assert count == 2
    finally:
        app.dependency_overrides.clear()


def test_submit_correction_without_membership_is_rejected(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/corrections",
            json={
                "workspace_id": str(workspace_id),
                "answer_id": str(uuid.uuid4()),
                "notes": "Something is wrong."
            },
            headers={"x-dev-user-id": str(uuid.uuid4())},
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_submit_correction_for_an_answer_in_a_different_workspace_is_rejected(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        user_id = uuid.uuid4()
        owning_workspace_id = uuid.uuid4()
        other_workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            answer_id = _seed_workspace_with_answer(
                cursor, user_id=user_id, workspace_id=owning_workspace_id
            )
            cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (other_workspace_id,))
            cursor.execute(
                """
                INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                VALUES (%s, %s, %s, 'owner', 'active')
                """,
                (uuid.uuid4(), user_id, other_workspace_id),
            )
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/corrections",
            json={
                "workspace_id": str(other_workspace_id),
                "answer_id": str(answer_id),
                "notes": "Something is wrong."
            },
            headers={"x-dev-user-id": str(user_id)},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_submit_correction_with_empty_notes_is_rejected(postgres_connection) -> None:
    app.dependency_overrides[get_db_connection] = lambda: postgres_connection
    try:
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        with postgres_connection.cursor() as cursor:
            answer_id = _seed_workspace_with_answer(cursor, user_id=user_id, workspace_id=workspace_id)
        postgres_connection.commit()

        client = TestClient(app)
        response = client.post(
            "/corrections",
            json={"workspace_id": str(workspace_id), "answer_id": str(answer_id), "notes": ""},
            headers={"x-dev-user-id": str(user_id)},
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
