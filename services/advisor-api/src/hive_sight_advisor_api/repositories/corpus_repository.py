from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import psycopg


@dataclass(frozen=True)
class Passage:
    id: UUID
    corpus_document_id: UUID
    text_content: str
    distance: float
    document_title: str
    document_source: str
    document_source_url: str | None
    document_licence_terms: str
    document_status: str
    superseded_by_document_title: str | None


class CorpusRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def find_similar_passages(
        self, query_embedding: list[float], jurisdiction_id: UUID, limit: int = 1
    ) -> list[Passage]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    passages.id,
                    passages.corpus_document_id,
                    passages.text_content,
                    passages.embedding <=> %s::vector AS distance,
                    corpus_documents.title AS document_title,
                    corpus_documents.source AS document_source,
                    corpus_documents.source_url AS document_source_url,
                    corpus_documents.licence_terms AS document_licence_terms,
                    corpus_documents.status AS document_status,
                    superseding_document.title AS superseded_by_document_title
                FROM passages
                JOIN corpus_documents ON corpus_documents.id = passages.corpus_document_id
                LEFT JOIN corpus_documents AS superseding_document
                    ON superseding_document.id = corpus_documents.superseded_by_corpus_document_id
                WHERE corpus_documents.jurisdiction_id = %s
                    AND corpus_documents.status != 'retired'
                ORDER BY distance
                LIMIT %s
                """,
                (query_embedding, jurisdiction_id, limit),
            )
            rows = cursor.fetchall()
        return [
            Passage(
                id=row[0],
                corpus_document_id=row[1],
                text_content=row[2],
                distance=row[3],
                document_title=row[4],
                document_source=row[5],
                document_source_url=row[6],
                document_licence_terms=row[7],
                document_status=row[8],
                superseded_by_document_title=row[9],
            )
            for row in rows
        ]
