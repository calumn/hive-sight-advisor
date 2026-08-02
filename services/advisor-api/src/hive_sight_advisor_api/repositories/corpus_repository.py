from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import psycopg


@dataclass(frozen=True)
class Passage:
    id: UUID
    corpus_document_id: UUID
    text_content: str


class CorpusRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def find_similar_passages(
        self, query_embedding: list[float], jurisdiction_id: UUID, limit: int = 1
    ) -> list[Passage]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT passages.id, passages.corpus_document_id, passages.text_content
                FROM passages
                JOIN corpus_documents ON corpus_documents.id = passages.corpus_document_id
                WHERE corpus_documents.jurisdiction_id = %s
                ORDER BY passages.embedding <=> %s::vector
                LIMIT %s
                """,
                (jurisdiction_id, query_embedding, limit),
            )
            rows = cursor.fetchall()
        return [Passage(id=row[0], corpus_document_id=row[1], text_content=row[2]) for row in rows]
