import uuid

from hive_sight_advisor_api.repositories.jurisdiction_repository import JurisdictionRepository


def test_find_id_by_code_returns_the_matching_jurisdiction_id(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
    postgres_connection.commit()

    repository = JurisdictionRepository(postgres_connection)
    found = repository.find_id_by_code("uk")

    assert found == jurisdiction_id


def test_find_id_by_code_returns_none_for_an_unknown_code(postgres_connection) -> None:
    repository = JurisdictionRepository(postgres_connection)

    found = repository.find_id_by_code("de")

    assert found is None
