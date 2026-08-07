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
    assert results[0].distance < 0.01


def test_find_similar_passages_reports_a_large_distance_for_an_unrelated_query(
    postgres_connection,
) -> None:
    jurisdiction_id = uuid.uuid4()
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()

    passage_embedding = _embedding((0, 1.0))
    unrelated_query_embedding = _embedding((500, 1.0))

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
            (corpus_document_id, jurisdiction_id, "Varroa Guide", "APHA BeeBase", "Open Government Licence"),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (passage_id, corpus_document_id, "Passage text", passage_embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(
        unrelated_query_embedding, jurisdiction_id=jurisdiction_id, limit=1
    )

    assert len(results) == 1
    assert results[0].distance > 0.9


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


def test_find_similar_passages_returns_the_documents_provenance(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = _embedding((0, 1.0))

    with postgres_connection.cursor() as cursor:
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
                "Managing Varroa: A Guide for UK Beekeepers",
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
            (passage_id, corpus_document_id, "Passage text", embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(embedding, jurisdiction_id=jurisdiction_id, limit=1)

    assert len(results) == 1
    passage = results[0]
    assert passage.document_title == "Managing Varroa: A Guide for UK Beekeepers"
    assert passage.document_source == "APHA BeeBase"
    assert passage.document_source_url == "https://www.nationalbeeunit.com/"
    assert passage.document_licence_terms == "Open Government Licence"
    assert passage.document_status == "active"
    assert passage.superseded_by_document_title is None


def test_find_similar_passages_flags_a_superseded_documents_passage(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    old_document_id = uuid.uuid4()
    new_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = _embedding((0, 1.0))

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
            (new_document_id, jurisdiction_id, "Managing Varroa (2024 edition)", "APHA BeeBase", "Open Government Licence"),
        )
        cursor.execute(
            """
            INSERT INTO corpus_documents
                (id, jurisdiction_id, title, source, licence_terms, status, superseded_by_corpus_document_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                old_document_id,
                jurisdiction_id,
                "Managing Varroa (2018 edition)",
                "APHA BeeBase",
                "Open Government Licence",
                "superseded",
                new_document_id,
            ),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, embedding)
            VALUES (%s, %s, %s, %s)
            """,
            (passage_id, old_document_id, "Old passage text", embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(embedding, jurisdiction_id=jurisdiction_id, limit=1)

    assert len(results) == 1
    passage = results[0]
    assert passage.id == passage_id
    assert passage.document_status == "superseded"
    assert passage.superseded_by_document_title == "Managing Varroa (2024 edition)"


def test_find_similar_passages_ranks_the_sub_topic_matching_passage_over_a_sibling(
    postgres_connection,
) -> None:
    # A single Corpus Document curated as multiple Passages (chunking, Slice 0012):
    # a query about one sub-topic must retrieve that sub-topic's Passage, not a
    # sibling Passage from the same Document that happens to be document-adjacent
    # but topically different.
    jurisdiction_id = uuid.uuid4()
    corpus_document_id = uuid.uuid4()
    monitoring_passage_id = uuid.uuid4()
    timing_passage_id = uuid.uuid4()

    monitoring_embedding = _embedding((0, 1.0), (1, 0.05))
    timing_embedding = _embedding((0, 0.05), (1, 1.0))
    monitoring_query_embedding = _embedding((0, 0.95), (1, 0.1))

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
            (
                corpus_document_id,
                jurisdiction_id,
                "Seasonal Varroa Management: A Guide for UK Beekeepers",
                "APHA BeeBase",
                "Open Government Licence",
            ),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, position, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (monitoring_passage_id, corpus_document_id, "Monitoring passage text", 0, monitoring_embedding),
        )
        cursor.execute(
            """
            INSERT INTO passages (id, corpus_document_id, text_content, position, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (timing_passage_id, corpus_document_id, "Seasonal timing passage text", 1, timing_embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(
        monitoring_query_embedding, jurisdiction_id=jurisdiction_id, limit=1
    )

    assert len(results) == 1
    assert results[0].id == monitoring_passage_id
    assert results[0].text_content == "Monitoring passage text"


def test_find_similar_passages_never_returns_a_retired_documents_passage(postgres_connection) -> None:
    jurisdiction_id = uuid.uuid4()
    retired_document_id = uuid.uuid4()
    active_document_id = uuid.uuid4()
    retired_passage_id = uuid.uuid4()
    active_passage_id = uuid.uuid4()

    # The retired passage is the closer match; if retirement isn't respected, it would be
    # returned as the closest result instead of the more distant active one.
    retired_embedding = _embedding((0, 1.0))
    active_embedding = _embedding((0, 0.6), (1, 0.4))
    query_embedding = _embedding((0, 1.0))

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
        cursor.execute(
            """
            INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms, status)
            VALUES (%s, %s, %s, %s, %s, 'retired')
            """,
            (retired_document_id, jurisdiction_id, "Withdrawn Guide", "APHA BeeBase", "Open Government Licence"),
        )
        cursor.execute(
            """
            INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (active_document_id, jurisdiction_id, "Current Guide", "APHA BeeBase", "Open Government Licence"),
        )
        cursor.execute(
            "INSERT INTO passages (id, corpus_document_id, text_content, embedding) VALUES (%s, %s, %s, %s)",
            (retired_passage_id, retired_document_id, "Withdrawn passage text", retired_embedding),
        )
        cursor.execute(
            "INSERT INTO passages (id, corpus_document_id, text_content, embedding) VALUES (%s, %s, %s, %s)",
            (active_passage_id, active_document_id, "Current passage text", active_embedding),
        )
    postgres_connection.commit()

    repository = CorpusRepository(postgres_connection)
    results = repository.find_similar_passages(
        query_embedding, jurisdiction_id=jurisdiction_id, limit=5
    )

    assert [passage.id for passage in results] == [active_passage_id]
