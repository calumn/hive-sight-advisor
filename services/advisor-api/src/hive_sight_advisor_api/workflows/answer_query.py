from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.generation_provider import GenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository


@dataclass(frozen=True)
class Citation:
    id: UUID
    answer_id: UUID
    passage_id: UUID


@dataclass(frozen=True)
class Answer:
    id: UUID
    query_id: UUID
    text: str
    grounding_status: str
    citations: list[Citation]


class QueryRepository(Protocol):
    def save(
        self,
        workspace_id: UUID,
        query_id: UUID,
        query_text: str,
        jurisdiction_id: UUID,
        answer: Answer,
    ) -> None: ...


class AnswerQueryWorkflow:
    def __init__(
        self,
        corpus_repository: CorpusRepository,
        embedding_provider: EmbeddingProvider,
        generation_provider: GenerationProvider,
        query_repository: QueryRepository,
    ) -> None:
        self._corpus_repository = corpus_repository
        self._embedding_provider = embedding_provider
        self._generation_provider = generation_provider
        self._query_repository = query_repository

    def answer_query(self, workspace_id: UUID, query_text: str, jurisdiction_id: UUID) -> Answer:
        query_id = uuid4()
        query_embedding = self._embedding_provider.embed(query_text)
        passages = self._corpus_repository.find_similar_passages(
            query_embedding, jurisdiction_id=jurisdiction_id, limit=1
        )
        generated = self._generation_provider.generate_answer(query_text, passages)

        answer_id = uuid4()
        citations = [
            Citation(id=uuid4(), answer_id=answer_id, passage_id=passage_id)
            for passage_id in generated.cited_passage_ids
        ]
        answer = Answer(
            id=answer_id,
            query_id=query_id,
            text=generated.text,
            grounding_status="grounded" if citations else "ungrounded",
            citations=citations,
        )
        self._query_repository.save(workspace_id, query_id, query_text, jurisdiction_id, answer)
        return answer
