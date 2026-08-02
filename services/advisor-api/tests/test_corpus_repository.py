import uuid

from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository


def _embedding(*nonzero_dims: tuple[int, float]) -> list[float]:
    vector = [0.0] * 1024
    for index, value in nonzero_dims:
        vector[index] = value
    return vector


def test_find_similar_passages_returns_the_closest_seeded_passage(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    corpus_document_id = uuid.uuid4()
    close_passage_id = uuid.uuid4()
    far_passage_id = uuid.uuid4()

    close_embedding = _embedding((0, 1.0), (1, 0.05))
    far_embedding = _embedding((0, 0.05), (1, 1.0))
    query_embedding = _embedding((0, 0.9), (1, 0.1))

    with postgres_connection.cursor() as cursor:
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
            (close_passage_id, corpus_document_id, "Close passage text", close_embedding),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (far_passage_id, corpus_document_id, "Far passage text", far_embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(
        query_embedding, jurisdiction_id=jurisdiction_id, limit=1
    )

    assert len(results) == 1
    assert results[0].id == close_passage_id
    assert results[0].text_content == "Close passage text"


def test_find_similar_passages_never_returns_a_different_jurisdictions_passage(
    postgres_connection,
) -> None:
    jurisdiction_a_id = uuid.uuid4()
    jurisdiction_b_id = uuid.uuid4()
    document_a_id = uuid.uuid4()
    document_b_id = uuid.uuid4()
    passage_a_id = uuid.uuid4()
    passage_b_id = uuid.uuid4()

    # Passage B is the globally closer match to the query embedding (exact match,
    # distance 0), but it belongs to a different jurisdiction. A query scoped to
    # jurisdiction A must return Passage A anyway, never B.
    passage_a_embedding = _embedding((0, 0.5), (1, 0.5))
    passage_b_embedding = _embedding((0, 1.0))
    query_embedding = _embedding((0, 1.0))

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_a_id, "uk", "United Kingdom"),
        )
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_b_id, "us", "United States"),
        )
        cursor.execute(
            """
            INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (document_a_id, jurisdiction_a_id, "UK Guide", "APHA BeeBase", "Open Government Licence"),
        )
        cursor.execute(
            """
            INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (document_b_id, jurisdiction_b_id, "US Guide", "HBHC", "CC BY-NC-ND"),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (passage_a_id, document_a_id, "UK passage text", passage_a_embedding),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (passage_b_id, document_b_id, "US passage text", passage_b_embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(
        query_embedding, jurisdiction_id=jurisdiction_a_id, limit=1
    )

    assert len(results) == 1
    assert results[0].id == passage_a_id
    assert results[0].text_content == "UK passage text"
