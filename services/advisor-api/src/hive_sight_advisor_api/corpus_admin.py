from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import yaml
from pgvector.psycopg import register_vector

from hive_sight_advisor_api.adapters.corpus_review_claude import ClaudeCorpusReviewProvider
from hive_sight_advisor_api.adapters.corpus_review_provider import CorpusReviewProvider
from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository
from hive_sight_advisor_api.settings import load_settings

# Anchored to this package's location rather than a bare relative path — a relative
# default silently resolved against whatever directory the CLI happened to be invoked
# from, which could write a stray duplicate file instead of updating the single
# canonical, source-controlled ledger the Corpus Curator CLI Tooling decision depends on.
DEFAULT_DATA_FILE = Path(__file__).parents[4] / "scripts" / "curator_added_documents.yaml"


@dataclass(frozen=True)
class PassageCandidate:
    id: UUID
    text: str
    embedding: list[float]
    advisory: str


@dataclass(frozen=True)
class PreparedCandidate:
    document_id: UUID
    jurisdiction_id: UUID
    jurisdiction_code: str
    title: str
    source: str
    source_url: str | None
    licence_terms: str
    passages: list[PassageCandidate]


def _find_jurisdiction(connection: psycopg.Connection, jurisdiction_code: str) -> tuple[UUID, str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, display_name FROM jurisdictions WHERE code = %s", (jurisdiction_code,)
        )
        row = cursor.fetchone()
    if row is None:
        raise ValueError(f"No jurisdiction found with code {jurisdiction_code!r}.")
    return row[0], row[1]


def _load_yaml_data(yaml_path: Path) -> dict:
    if not yaml_path.exists():
        return {"documents": [], "retired_document_ids": []}
    data = yaml.safe_load(yaml_path.read_text()) or {}
    data.setdefault("documents", [])
    data.setdefault("retired_document_ids", [])
    return data


def _save_yaml_data(yaml_path: Path, data: dict) -> None:
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(yaml.safe_dump(data, sort_keys=False))


def prepare_candidate(
    connection: psycopg.Connection,
    embedding_provider: EmbeddingProvider,
    review_provider: CorpusReviewProvider,
    jurisdiction_code: str,
    title: str,
    source: str,
    source_url: str | None,
    licence_terms: str,
    passage_texts: list[str],
    nearby_limit: int = 3,
) -> PreparedCandidate:
    register_vector(connection)
    jurisdiction_id, jurisdiction_display_name = _find_jurisdiction(connection, jurisdiction_code)
    corpus_repository = CorpusRepository(connection)

    passages = []
    for passage_text in passage_texts:
        embedding = embedding_provider.embed(passage_text)
        nearby_passages = corpus_repository.find_similar_passages(
            embedding, jurisdiction_id=jurisdiction_id, limit=nearby_limit
        )
        advisory = review_provider.review_candidate(
            candidate_text=passage_text,
            jurisdiction_display_name=jurisdiction_display_name,
            nearby_passages=nearby_passages,
        )
        passages.append(
            PassageCandidate(id=uuid4(), text=passage_text, embedding=embedding, advisory=advisory)
        )

    return PreparedCandidate(
        document_id=uuid4(),
        jurisdiction_id=jurisdiction_id,
        jurisdiction_code=jurisdiction_code,
        title=title,
        source=source,
        source_url=source_url,
        licence_terms=licence_terms,
        passages=passages,
    )


def commit_candidate(
    connection: psycopg.Connection, candidate: PreparedCandidate, yaml_path: Path
) -> None:
    register_vector(connection)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                candidate.document_id,
                candidate.jurisdiction_id,
                candidate.title,
                candidate.source,
                candidate.source_url,
                candidate.licence_terms,
            ),
        )
        for position, passage in enumerate(candidate.passages):
            cursor.execute(
                """
                INSERT INTO passages (id, corpus_document_id, text_content, position, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    passage.id,
                    candidate.document_id,
                    passage.text,
                    position,
                    passage.embedding,
                ),
            )
    connection.commit()

    data = _load_yaml_data(yaml_path)
    data["documents"].append(
        {
            "id": str(candidate.document_id),
            "jurisdiction_code": candidate.jurisdiction_code,
            "title": candidate.title,
            "source": candidate.source,
            "source_url": candidate.source_url,
            "licence_terms": candidate.licence_terms,
            "passages": [{"id": str(passage.id), "text": passage.text} for passage in candidate.passages],
        }
    )
    _save_yaml_data(yaml_path, data)


def retire_document(
    connection: psycopg.Connection,
    yaml_path: Path,
    *,
    document_id: UUID | None = None,
    title: str | None = None,
) -> UUID:
    if document_id is None and title is None:
        raise ValueError("Provide either document_id or title.")

    with connection.cursor() as cursor:
        if document_id is not None:
            cursor.execute("SELECT id FROM corpus_documents WHERE id = %s", (document_id,))
        else:
            cursor.execute("SELECT id FROM corpus_documents WHERE title = %s", (title,))
        row = cursor.fetchone()
        if row is None:
            identifier = document_id if document_id is not None else title
            raise ValueError(f"No Corpus Document found matching {identifier!r}.")
        resolved_id = row[0]

        cursor.execute(
            "UPDATE corpus_documents SET status = 'retired' WHERE id = %s", (resolved_id,)
        )
    connection.commit()

    data = _load_yaml_data(yaml_path)
    if str(resolved_id) not in data["retired_document_ids"]:
        data["retired_document_ids"].append(str(resolved_id))
    _save_yaml_data(yaml_path, data)

    return resolved_id


def apply_curator_documents(
    connection: psycopg.Connection,
    embedding_provider: EmbeddingProvider,
    yaml_path: Path,
) -> None:
    register_vector(connection)
    data = _load_yaml_data(yaml_path)

    for document in data["documents"]:
        jurisdiction_id, _ = _find_jurisdiction(connection, document["jurisdiction_code"])
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    source = EXCLUDED.source,
                    source_url = EXCLUDED.source_url,
                    licence_terms = EXCLUDED.licence_terms
                """,
                (
                    UUID(document["id"]),
                    jurisdiction_id,
                    document["title"],
                    document["source"],
                    document["source_url"],
                    document["licence_terms"],
                ),
            )
            for position, passage in enumerate(document["passages"]):
                embedding = embedding_provider.embed(passage["text"])
                cursor.execute(
                    """
                    INSERT INTO passages (id, corpus_document_id, text_content, position, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        position = EXCLUDED.position,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        UUID(passage["id"]),
                        UUID(document["id"]),
                        passage["text"],
                        position,
                        embedding,
                    ),
                )
        connection.commit()

    if data["retired_document_ids"]:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE corpus_documents SET status = 'retired' WHERE id = ANY(%s)",
                ([UUID(doc_id) for doc_id in data["retired_document_ids"]],),
            )
        connection.commit()


def _read_passage_texts(texts: list[str] | None, text_files: list[str] | None) -> list[str]:
    if text_files:
        return [Path(text_file).read_text().strip() for text_file in text_files]
    if texts:
        return list(texts)
    raise SystemExit("Provide --text (repeatable, one per passage) or --text-file (repeatable).")


def main() -> None:
    parser = argparse.ArgumentParser(description="HiveSight Advisor corpus admin CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add-document")
    add_parser.add_argument("--jurisdiction", required=True, help="Jurisdiction code, e.g. uk/us")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--source", required=True)
    add_parser.add_argument("--source-url", default=None)
    add_parser.add_argument("--licence-terms", required=True)
    add_parser.add_argument(
        "--text", action="append", help="Text for one passage. Repeat once per passage chunk."
    )
    add_parser.add_argument(
        "--text-file", action="append", help="Path to a passage's text. Repeat once per passage chunk."
    )
    add_parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    add_parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)

    retire_parser = subparsers.add_parser("retire-document")
    retire_parser.add_argument("--document-id")
    retire_parser.add_argument("--title")
    retire_parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)

    args = parser.parse_args()
    settings = load_settings()
    if not settings.voyage_api_key or not settings.anthropic_api_key:
        raise SystemExit("Set VOYAGE_API_KEY and ANTHROPIC_API_KEY before running this tool.")

    connection = psycopg.connect(settings.database_url)
    register_vector(connection)

    if args.command == "add-document":
        passage_texts = _read_passage_texts(args.text, args.text_file)
        candidate = prepare_candidate(
            connection,
            embedding_provider=VoyageEmbeddingProvider(api_key=settings.voyage_api_key),
            review_provider=ClaudeCorpusReviewProvider(api_key=settings.anthropic_api_key),
            jurisdiction_code=args.jurisdiction,
            title=args.title,
            source=args.source,
            source_url=args.source_url,
            licence_terms=args.licence_terms,
            passage_texts=passage_texts,
        )
        print("\n--- AI-assisted review (advisory only — you decide) ---")
        for index, passage in enumerate(candidate.passages, start=1):
            print(f"[chunk {index}/{len(candidate.passages)}]")
            print(passage.advisory)
        print("---\n")
        if not args.yes:
            confirmation = input(
                f'Add "{candidate.title}" ({len(candidate.passages)} passage(s)) to the corpus? [y/N] '
            ).strip().lower()
            if confirmation != "y":
                print("Not added.")
                return
        commit_candidate(connection, candidate, Path(args.data_file))
        print(f"Added document {candidate.document_id} ({len(candidate.passages)} passage(s)).")
    elif args.command == "retire-document":
        document_id = UUID(args.document_id) if args.document_id else None
        resolved_id = retire_document(
            connection, Path(args.data_file), document_id=document_id, title=args.title
        )
        print(f"Retired document {resolved_id}.")


if __name__ == "__main__":
    main()
