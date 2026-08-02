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
