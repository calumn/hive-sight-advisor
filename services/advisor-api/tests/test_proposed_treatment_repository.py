import uuid

from hive_sight_advisor_api.repositories.proposed_treatment_repository import (
    ProposedTreatmentRepository,
)


def _seed_answer(cursor, *, jurisdiction_id) -> uuid.UUID:
    workspace_id = uuid.uuid4()
    query_id = uuid.uuid4()
    answer_id = uuid.uuid4()
    cursor.execute("INSERT INTO workspaces (id) VALUES (%s)", (workspace_id,))
    cursor.execute(
        "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (jurisdiction_id, "uk", "United Kingdom"),
    )
    cursor.execute(
        "INSERT INTO queries (id, workspace_id, text) VALUES (%s, %s, %s)",
        (query_id, workspace_id, "What should I do about high mite counts?"),
    )
    cursor.execute(
        "INSERT INTO answers (id, query_id, text, grounding_status) VALUES (%s, %s, %s, %s)",
        (answer_id, query_id, "Apply oxalic acid vaporisation.", "grounded"),
    )
    return answer_id


def test_save_persists_a_suggested_proposed_treatment(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, jurisdiction_id=jurisdiction_id)
    postgres_connection.commit()

    repository = ProposedTreatmentRepository(postgres_connection)
    proposed_treatment = repository.save(
        hive_id="hivesight-hive-42",
        jurisdiction_id=jurisdiction_id,
        answer_id=answer_id,
    )

    assert proposed_treatment.hive_id == "hivesight-hive-42"
    assert proposed_treatment.status == "suggested"
    assert proposed_treatment.completed_at is None


def test_mark_completed_transitions_status(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, jurisdiction_id=jurisdiction_id)
    postgres_connection.commit()

    repository = ProposedTreatmentRepository(postgres_connection)
    proposed_treatment = repository.save(
        hive_id="hivesight-hive-42",
        jurisdiction_id=jurisdiction_id,
        answer_id=answer_id,
    )

    completed = repository.mark_completed(proposed_treatment.id)

    assert completed is not None
    assert completed.status == "completed"
    assert completed.completed_at is not None


def test_find_latest_suggested_by_hive_returns_the_suggestion(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, jurisdiction_id=jurisdiction_id)
    postgres_connection.commit()

    repository = ProposedTreatmentRepository(postgres_connection)
    saved = repository.save(
        hive_id="hivesight-hive-42",
        jurisdiction_id=jurisdiction_id,
        answer_id=answer_id,
    )

    found = repository.find_latest_suggested_by_hive("hivesight-hive-42")

    assert found is not None
    assert found.id == saved.id


def test_find_latest_suggested_by_hive_returns_none_when_no_suggestion_exists(
    postgres_connection,
) -> None:
    repository = ProposedTreatmentRepository(postgres_connection)

    found = repository.find_latest_suggested_by_hive("no-such-hive")

    assert found is None


def test_find_by_id_returns_the_treatment_regardless_of_status(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        answer_id = _seed_answer(cursor, jurisdiction_id=jurisdiction_id)
    postgres_connection.commit()

    repository = ProposedTreatmentRepository(postgres_connection)
    saved = repository.save(
        hive_id="hivesight-hive-42",
        jurisdiction_id=jurisdiction_id,
        answer_id=answer_id,
    )
    repository.mark_completed(saved.id)

    found = repository.find_by_id(saved.id)

    assert found is not None
    assert found.status == "completed"


def test_find_by_id_returns_none_when_not_found(postgres_connection) -> None:
    repository = ProposedTreatmentRepository(postgres_connection)

    found = repository.find_by_id(uuid.uuid4())

    assert found is None
