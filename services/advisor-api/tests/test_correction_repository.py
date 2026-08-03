import uuid

from hive_sight_advisor_api.repositories.correction_repository import CorrectionRepository


def _seed_answer(cursor, *, workspace_id, jurisdiction_id=None) -> uuid.UUID:
    query_id = uuid.uuid4()
    answer_id = uuid.uuid4()
    cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
    cursor.execute(
        "INSERT INTO queries (id, workspace_id, text) VALUES (%s, %s, %s)",
        (query_id, workspace_id, "How do I treat varroa?"),
    )
    cursor.execute(
        "INSERT INTO answers (id, query_id, text, grounding_status) VALUES (%s, %s, %s, %s)",
        (answer_id, query_id, "Some answer text.", "grounded"),
    )
    return answer_id


def test_save_persists_a_trusted_correction(postgres_connection) -> None:
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, workspace_id=workspace_id)
        cursor.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
    postgres_connection.commit()

    repository = CorrectionRepository(postgres_connection)
    correction = repository.save(
        workspace_id=workspace_id,
        answer_id=answer_id,
        created_by_user_id=user_id,
        notes="This cites the wrong jurisdiction's guidance.",
    )

    assert correction.status == "trusted"
    assert correction.notes == "This cites the wrong jurisdiction's guidance."

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT workspace_id, answer_id, created_by_user_id, notes, status FROM corrections WHERE id = %s",
            (correction.id,),
        )
        row = cursor.fetchone()

    assert row == (workspace_id, answer_id, user_id, "This cites the wrong jurisdiction's guidance.", "trusted")


def test_save_allows_multiple_corrections_for_the_same_answer(postgres_connection) -> None:
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, workspace_id=workspace_id)
        cursor.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
    postgres_connection.commit()

    repository = CorrectionRepository(postgres_connection)
    first = repository.save(
        workspace_id=workspace_id, answer_id=answer_id, created_by_user_id=user_id, notes="First issue."
    )
    second = repository.save(
        workspace_id=workspace_id, answer_id=answer_id, created_by_user_id=user_id, notes="Second issue."
    )

    assert first.id != second.id

    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM corrections WHERE answer_id = %s", (answer_id,))
        (count,) = cursor.fetchone()
    assert count == 2


def test_answer_belongs_to_workspace_is_true_for_the_owning_workspace(postgres_connection) -> None:
    workspace_id = uuid.uuid4()

    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, workspace_id=workspace_id)
    postgres_connection.commit()

    repository = CorrectionRepository(postgres_connection)

    assert repository.answer_belongs_to_workspace(answer_id, workspace_id) is True


def test_answer_belongs_to_workspace_is_false_for_a_different_workspace(postgres_connection) -> None:
    owning_workspace_id = uuid.uuid4()
    other_workspace_id = uuid.uuid4()

    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, workspace_id=owning_workspace_id)
        cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (other_workspace_id,))
    postgres_connection.commit()

    repository = CorrectionRepository(postgres_connection)

    assert repository.answer_belongs_to_workspace(answer_id, other_workspace_id) is False


def test_answer_belongs_to_workspace_is_false_for_a_nonexistent_answer(postgres_connection) -> None:
    workspace_id = uuid.uuid4()

    with postgres_connection.cursor() as cursor:
        cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
    postgres_connection.commit()

    repository = CorrectionRepository(postgres_connection)

    assert repository.answer_belongs_to_workspace(uuid.uuid4(), workspace_id) is False
