import uuid
from pathlib import Path

import pytest
import yaml

from hive_sight_advisor_api.corpus_admin import (
    apply_curator_documents,
    commit_candidate,
    prepare_candidate,
    retire_document,
)


class _StubEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        vector = [0.0] * 1024
        vector[0] = 1.0
        return vector


class _RecordingReviewProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def review_candidate(self, candidate_text, jurisdiction_display_name, nearby_passages):
        self.calls.append((candidate_text, jurisdiction_display_name, len(nearby_passages)))
        return f"advisory for {jurisdiction_display_name} ({len(nearby_passages)} nearby)"


def _seed_jurisdiction_with_document(cursor, *, code="uk", display_name="United Kingdom"):
    jurisdiction_id = uuid.uuid4()
    document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = [0.0] * 1024
    embedding[0] = 1.0
    cursor.execute(
        "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
        (jurisdiction_id, code, display_name),
    )
    cursor.execute(
        """
        INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (document_id, jurisdiction_id, "Existing Document", "Existing Source", "Existing Licence"),
    )
    cursor.execute(
        "INSERT INTO passages (id, corpus_document_id, text_content, embedding) VALUES (%s, %s, %s, %s)",
        (passage_id, document_id, "Existing passage text.", embedding),
    )
    return jurisdiction_id, document_id


def test_prepare_candidate_embeds_and_reviews_against_nearby_passages(postgres_connection) -> None:
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()

    review_provider = _RecordingReviewProvider()
    candidate = prepare_candidate(
        postgres_connection,
        embedding_provider=_StubEmbeddingProvider(),
        review_provider=review_provider,
        jurisdiction_code="uk",
        title="New Document",
        source="New Source",
        source_url="https://example.com/new",
        licence_terms="New Licence",
        passage_texts=["New candidate passage text."],
    )

    assert candidate.title == "New Document"
    assert candidate.jurisdiction_code == "uk"
    assert len(candidate.passages) == 1
    assert candidate.document_id != candidate.passages[0].id
    assert candidate.passages[0].advisory == "advisory for United Kingdom (1 nearby)"
    assert review_provider.calls == [("New candidate passage text.", "United Kingdom", 1)]


def test_prepare_candidate_reviews_each_passage_chunk_independently(postgres_connection) -> None:
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()

    review_provider = _RecordingReviewProvider()
    candidate = prepare_candidate(
        postgres_connection,
        embedding_provider=_StubEmbeddingProvider(),
        review_provider=review_provider,
        jurisdiction_code="uk",
        title="Multi-Chunk Document",
        source="New Source",
        source_url=None,
        licence_terms="New Licence",
        passage_texts=["First chunk text.", "Second chunk text."],
    )

    assert [passage.text for passage in candidate.passages] == ["First chunk text.", "Second chunk text."]
    assert len({passage.id for passage in candidate.passages}) == 2
    assert [call[0] for call in review_provider.calls] == ["First chunk text.", "Second chunk text."]


def test_prepare_candidate_raises_for_unknown_jurisdiction_code(postgres_connection) -> None:
    with pytest.raises(ValueError, match="jurisdiction"):
        prepare_candidate(
            postgres_connection,
            embedding_provider=_StubEmbeddingProvider(),
            review_provider=_RecordingReviewProvider(),
            jurisdiction_code="does-not-exist",
            title="New Document",
            source="New Source",
            source_url=None,
            licence_terms="New Licence",
            passage_texts=["New candidate passage text."],
        )


def test_commit_candidate_persists_document_and_passage_and_appends_to_yaml(
    postgres_connection, tmp_path
) -> None:
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()

    candidate = prepare_candidate(
        postgres_connection,
        embedding_provider=_StubEmbeddingProvider(),
        review_provider=_RecordingReviewProvider(),
        jurisdiction_code="uk",
        title="New Document",
        source="New Source",
        source_url="https://example.com/new",
        licence_terms="New Licence",
        passage_texts=["New candidate passage text."],
    )
    yaml_path = tmp_path / "curator_added_documents.yaml"

    commit_candidate(postgres_connection, candidate, yaml_path)

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT title, source, source_url, licence_terms, status FROM corpus_documents WHERE id = %s",
            (candidate.document_id,),
        )
        row = cursor.fetchone()
        assert row == ("New Document", "New Source", "https://example.com/new", "New Licence", "active")

        cursor.execute(
            "SELECT text_content FROM passages WHERE id = %s", (candidate.passages[0].id,)
        )
        (text_content,) = cursor.fetchone()
        assert text_content == "New candidate passage text."

    data = yaml.safe_load(yaml_path.read_text())
    assert data["documents"] == [
        {
            "id": str(candidate.document_id),
            "jurisdiction_code": "uk",
            "title": "New Document",
            "source": "New Source",
            "source_url": "https://example.com/new",
            "licence_terms": "New Licence",
            "passages": [{"id": str(candidate.passages[0].id), "text": "New candidate passage text."}],
        }
    ]


def test_commit_candidate_persists_multiple_passages_with_position_order(
    postgres_connection, tmp_path
) -> None:
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()

    candidate = prepare_candidate(
        postgres_connection,
        embedding_provider=_StubEmbeddingProvider(),
        review_provider=_RecordingReviewProvider(),
        jurisdiction_code="uk",
        title="Multi-Chunk Document",
        source="New Source",
        source_url=None,
        licence_terms="New Licence",
        passage_texts=["First chunk text.", "Second chunk text.", "Third chunk text."],
    )
    yaml_path = tmp_path / "curator_added_documents.yaml"

    commit_candidate(postgres_connection, candidate, yaml_path)

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT text_content FROM passages WHERE corpus_document_id = %s ORDER BY position",
            (candidate.document_id,),
        )
        rows = [row[0] for row in cursor.fetchall()]
    assert rows == ["First chunk text.", "Second chunk text.", "Third chunk text."]

    data = yaml.safe_load(yaml_path.read_text())
    assert [passage["text"] for passage in data["documents"][0]["passages"]] == [
        "First chunk text.",
        "Second chunk text.",
        "Third chunk text.",
    ]


def test_retire_document_by_title_marks_status_and_appends_to_yaml(
    postgres_connection, tmp_path
) -> None:
    with postgres_connection.cursor() as cursor:
        _jurisdiction_id, document_id = _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()
    yaml_path = tmp_path / "curator_added_documents.yaml"

    retired_id = retire_document(postgres_connection, yaml_path, title="Existing Document")

    assert retired_id == document_id
    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT status FROM corpus_documents WHERE id = %s", (document_id,))
        (status,) = cursor.fetchone()
        assert status == "retired"

    data = yaml.safe_load(yaml_path.read_text())
    assert data["retired_document_ids"] == [str(document_id)]


def test_retire_document_by_id(postgres_connection, tmp_path) -> None:
    with postgres_connection.cursor() as cursor:
        _jurisdiction_id, document_id = _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()
    yaml_path = tmp_path / "curator_added_documents.yaml"

    retired_id = retire_document(postgres_connection, yaml_path, document_id=document_id)

    assert retired_id == document_id


def test_retire_document_raises_for_unknown_document(postgres_connection, tmp_path) -> None:
    yaml_path = tmp_path / "curator_added_documents.yaml"

    with pytest.raises(ValueError, match="No Corpus Document"):
        retire_document(postgres_connection, yaml_path, title="Does Not Exist")


def test_apply_curator_documents_seeds_documents_from_yaml(postgres_connection, tmp_path) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
    postgres_connection.commit()

    document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    yaml_path = tmp_path / "curator_added_documents.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "documents": [
                    {
                        "id": str(document_id),
                        "jurisdiction_code": "uk",
                        "title": "Curator Added Document",
                        "source": "Curator Source",
                        "source_url": "https://example.com/curator",
                        "licence_terms": "Curator Licence",
                        "passages": [{"id": str(passage_id), "text": "Curator-added passage text."}],
                    }
                ],
                "retired_document_ids": [],
            }
        )
    )

    apply_curator_documents(postgres_connection, _StubEmbeddingProvider(), yaml_path)

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT title, source, source_url, licence_terms, status FROM corpus_documents WHERE id = %s",
            (document_id,),
        )
        row = cursor.fetchone()
        assert row == (
            "Curator Added Document",
            "Curator Source",
            "https://example.com/curator",
            "Curator Licence",
            "active",
        )
        cursor.execute("SELECT text_content FROM passages WHERE id = %s", (passage_id,))
        (text_content,) = cursor.fetchone()
        assert text_content == "Curator-added passage text."


def test_apply_curator_documents_seeds_multiple_passages_per_document_in_position_order(
    postgres_connection, tmp_path
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
    postgres_connection.commit()

    document_id = uuid.uuid4()
    first_passage_id = uuid.uuid4()
    second_passage_id = uuid.uuid4()
    yaml_path = tmp_path / "curator_added_documents.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "documents": [
                    {
                        "id": str(document_id),
                        "jurisdiction_code": "uk",
                        "title": "Multi-Chunk Document",
                        "source": "Curator Source",
                        "source_url": None,
                        "licence_terms": "Curator Licence",
                        "passages": [
                            {"id": str(first_passage_id), "text": "First chunk text."},
                            {"id": str(second_passage_id), "text": "Second chunk text."},
                        ],
                    }
                ],
                "retired_document_ids": [],
            }
        )
    )

    apply_curator_documents(postgres_connection, _StubEmbeddingProvider(), yaml_path)

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, text_content, position FROM passages WHERE corpus_document_id = %s ORDER BY position",
            (document_id,),
        )
        rows = cursor.fetchall()
    assert rows == [
        (first_passage_id, "First chunk text.", 0),
        (second_passage_id, "Second chunk text.", 1),
    ]


def test_apply_curator_documents_retires_a_document_regardless_of_origin(
    postgres_connection, tmp_path
) -> None:
    with postgres_connection.cursor() as cursor:
        _jurisdiction_id, baseline_document_id = _seed_jurisdiction_with_document(cursor)
    postgres_connection.commit()

    yaml_path = tmp_path / "curator_added_documents.yaml"
    yaml_path.write_text(
        yaml.safe_dump({"documents": [], "retired_document_ids": [str(baseline_document_id)]})
    )

    apply_curator_documents(postgres_connection, _StubEmbeddingProvider(), yaml_path)

    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT status FROM corpus_documents WHERE id = %s", (baseline_document_id,))
        (status,) = cursor.fetchone()
    assert status == "retired"


def test_apply_curator_documents_is_a_noop_when_the_yaml_file_is_missing(
    postgres_connection, tmp_path
) -> None:
    yaml_path = tmp_path / "does_not_exist.yaml"

    apply_curator_documents(postgres_connection, _StubEmbeddingProvider(), yaml_path)


def test_default_data_file_resolves_to_the_repo_root_regardless_of_cwd() -> None:
    from hive_sight_advisor_api.corpus_admin import DEFAULT_DATA_FILE

    assert Path(DEFAULT_DATA_FILE).is_absolute()
    assert Path(DEFAULT_DATA_FILE).name == "curator_added_documents.yaml"
    assert Path(DEFAULT_DATA_FILE).parent.name == "scripts"
