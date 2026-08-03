from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.generation_provider import GenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository

# Provisional distance thresholds (cosine distance from pgvector's `<=>` operator),
# calibrated against a handful of real Voyage AI queries run against the seeded
# Passages, not a properly tuned dataset. See requirements/decision-log.md,
# "FR-008 Grounding Classification Mechanism". Configurable via Settings because the
# stub embedding provider's distances sit on a different scale than Voyage's; the
# acceptance-test environment overrides these to stub-appropriate values.
DEFAULT_GROUNDED_DISTANCE_THRESHOLD = 0.35
DEFAULT_PARTIAL_DISTANCE_THRESHOLD = 0.55

UNGROUNDED_ANSWER_TEXT = (
    "I don't have a grounded answer to that in the seeded corpus for this jurisdiction."
)


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
        grounded_distance_threshold: float = DEFAULT_GROUNDED_DISTANCE_THRESHOLD,
        partial_distance_threshold: float = DEFAULT_PARTIAL_DISTANCE_THRESHOLD,
    ) -> None:
        self._corpus_repository = corpus_repository
        self._embedding_provider = embedding_provider
        self._generation_provider = generation_provider
        self._query_repository = query_repository
        self._grounded_distance_threshold = grounded_distance_threshold
        self._partial_distance_threshold = partial_distance_threshold

    def answer_query(self, workspace_id: UUID, query_text: str, jurisdiction_id: UUID) -> Answer:
        query_id = uuid4()
        query_embedding = self._embedding_provider.embed(query_text)
        passages = self._corpus_repository.find_similar_passages(
            query_embedding, jurisdiction_id=jurisdiction_id, limit=1
        )
        closest_distance = passages[0].distance if passages else None

        if closest_distance is None or closest_distance > self._partial_distance_threshold:
            answer = Answer(
                id=uuid4(),
                query_id=query_id,
                text=UNGROUNDED_ANSWER_TEXT,
                grounding_status="ungrounded",
                citations=[],
            )
        else:
            generated = self._generation_provider.generate_answer(query_text, passages)
            answer_id = uuid4()
            citations = [
                Citation(id=uuid4(), answer_id=answer_id, passage_id=passage_id)
                for passage_id in generated.cited_passage_ids
            ]
            if not citations:
                grounding_status = "ungrounded"
            elif closest_distance > self._grounded_distance_threshold:
                grounding_status = "partial"
            else:
                grounding_status = "grounded"
            answer = Answer(
                id=answer_id,
                query_id=query_id,
                text=generated.text,
                grounding_status=grounding_status,
                citations=citations,
            )

        self._query_repository.save(workspace_id, query_id, query_text, jurisdiction_id, answer)
        return answer
