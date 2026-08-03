import uuid

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
        passage_text="New candidate passage text.",
    )

    assert candidate.title == "New Document"
    assert candidate.jurisdiction_code == "uk"
    assert candidate.document_id != candidate.passage_id
    assert candidate.advisory == "advisory for United Kingdom (1 nearby)"
    assert review_provider.calls == [("New candidate passage text.", "United Kingdom", 1)]


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
            passage_text="New candidate passage text.",
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
        passage_text="New candidate passage text.",
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
            "SELECT text_content FROM passages WHERE id = %s", (candidate.passage_id,)
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
            "passage_id": str(candidate.passage_id),
            "passage_text": "New candidate passage text.",
        }
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
                        "passage_id": str(passage_id),
                        "passage_text": "Curator-added passage text.",
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
