import uuid

from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.adapters.generation_provider import GeneratedAnswer
from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage
from hive_sight_advisor_api.workflows.answer_query import AnswerQueryWorkflow


def _passage(*, text_content: str, distance: float) -> Passage:
    return Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content=text_content,
        distance=distance,
        document_title="Managing Varroa: A Guide for UK Beekeepers",
        document_source="APHA BeeBase",
        document_source_url="https://www.nationalbeeunit.com/",
        document_licence_terms="Open Government Licence",
        document_status="active",
        superseded_by_document_title=None,
    )


class _FakeCorpusRepository:
    def __init__(self, passages: list[Passage]) -> None:
        self._passages = passages
        self.requested_limits: list[int] = []

    def find_similar_passages(self, query_embedding, jurisdiction_id, limit=1):
        self.requested_limits.append(limit)
        return self._passages[:limit]


class _FakeQueryRepository:
    def __init__(self) -> None:
        self.saved = None

    def save(self, workspace_id, query_id, query_text, jurisdiction_id, answer):
        self.saved = (workspace_id, query_id, query_text, jurisdiction_id, answer)


class _FakeGenerationProvider:
    def __init__(self, cited_passage_ids: list[uuid.UUID]) -> None:
        self._cited_passage_ids = cited_passage_ids

    def generate_answer(self, query_text, passages):
        return GeneratedAnswer(text="A generated answer.", cited_passage_ids=self._cited_passage_ids)


class _SpyGenerationProvider:
    def __init__(self) -> None:
        self.call_count = 0
        self._delegate = StubGenerationProvider()

    def generate_answer(self, query_text, passages):
        self.call_count += 1
        return self._delegate.generate_answer(query_text, passages)


def test_answer_query_orchestrates_embed_retrieve_generate_and_persist() -> None:
    passage = _passage(
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
        distance=0.1,
    )
    corpus_repository = _FakeCorpusRepository([passage])
    query_repository = _FakeQueryRepository()
    workflow = AnswerQueryWorkflow(
        corpus_repository=corpus_repository,
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=query_repository,
    )
    workspace_id = uuid.uuid4()
    jurisdiction_id = uuid.uuid4()

    answer = workflow.answer_query(
        workspace_id=workspace_id,
        query_text="How do I treat varroa?",
        jurisdiction_id=jurisdiction_id,
    )

    assert answer.grounding_status == "grounded"
    assert len(answer.citations) == 1
    assert answer.citations[0].passage_id == passage.id
    assert passage.text_content in answer.text
    assert query_repository.saved is not None
    saved_workspace_id, saved_query_id, saved_query_text, saved_jurisdiction_id, saved_answer = (
        query_repository.saved
    )
    assert saved_workspace_id == workspace_id
    assert saved_query_id == answer.query_id
    assert saved_query_text == "How do I treat varroa?"
    assert saved_jurisdiction_id == jurisdiction_id
    assert saved_answer is answer


def test_answer_query_is_ungrounded_and_skips_generation_when_nothing_is_close_enough() -> None:
    far_passage = _passage(
        text_content="Something entirely unrelated to the question.",
        distance=0.9,
    )
    generation_provider = _SpyGenerationProvider()
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([far_passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=generation_provider,
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="What is the capital of France?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "ungrounded"
    assert answer.citations == []
    assert generation_provider.call_count == 0


def test_answer_query_is_ungrounded_when_no_passage_exists_for_the_jurisdiction() -> None:
    generation_provider = _SpyGenerationProvider()
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=generation_provider,
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="How do I treat varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "ungrounded"
    assert answer.citations == []
    assert generation_provider.call_count == 0


def test_answer_query_is_partial_when_the_closest_passage_is_only_somewhat_related() -> None:
    related_passage = _passage(
        text_content="Adjacent guidance that does not directly answer the question.",
        distance=0.45,
    )
    generation_provider = _SpyGenerationProvider()
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([related_passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=generation_provider,
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="Should I paint my hive a different colour?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "partial"
    assert len(answer.citations) == 1
    assert answer.citations[0].passage_id == related_passage.id
    assert generation_provider.call_count == 1


def test_answer_query_carries_provenance_on_every_citation() -> None:
    passage = _passage(
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
        distance=0.1,
    )
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="How do I treat varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.document_title == passage.document_title
    assert citation.document_source == passage.document_source
    assert citation.document_source_url == passage.document_source_url
    assert citation.document_licence_terms == passage.document_licence_terms
    assert citation.is_superseded is False
    assert citation.superseded_by_document_title is None


def test_answer_query_flags_a_citation_from_a_superseded_source() -> None:
    passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content="Older Varroa guidance, still the closest match.",
        distance=0.1,
        document_title="Managing Varroa (2018 edition)",
        document_source="APHA BeeBase",
        document_source_url="https://www.nationalbeeunit.com/",
        document_licence_terms="Open Government Licence",
        document_status="superseded",
        superseded_by_document_title="Managing Varroa (2024 edition)",
    )
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="How do I treat varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "grounded"
    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.is_superseded is True
    assert citation.superseded_by_document_title == "Managing Varroa (2024 edition)"


def test_answer_query_retrieves_up_to_five_passages_for_comparison() -> None:
    closest = _passage(text_content="Oxalic acid guidance.", distance=0.1)
    second = _passage(text_content="Amitraz strip guidance.", distance=0.15)
    corpus_repository = _FakeCorpusRepository([closest, second])
    workflow = AnswerQueryWorkflow(
        corpus_repository=corpus_repository,
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="What are my options for treating varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert corpus_repository.requested_limits == [5]
    assert answer.grounding_status == "grounded"
    assert {citation.passage_id for citation in answer.citations} == {closest.id, second.id}


def test_answer_query_grounding_status_still_reflects_only_the_closest_passage() -> None:
    closest = _passage(text_content="Adjacent guidance, only partially related.", distance=0.45)
    second = _passage(text_content="A much closer match, but not the nearest.", distance=0.1)
    corpus_repository = _FakeCorpusRepository([closest, second])
    workflow = AnswerQueryWorkflow(
        corpus_repository=corpus_repository,
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="What are my options for treating varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "partial"


def test_answer_query_drops_a_cited_passage_id_that_was_not_retrieved() -> None:
    passage = _passage(text_content="Oxalic acid guidance.", distance=0.1)
    hallucinated_id = uuid.uuid4()
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=_FakeGenerationProvider(cited_passage_ids=[passage.id, hallucinated_id]),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="How do I treat varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "grounded"
    assert [citation.passage_id for citation in answer.citations] == [passage.id]


def test_answer_query_is_ungrounded_when_every_cited_passage_id_was_not_retrieved() -> None:
    passage = _passage(text_content="Oxalic acid guidance.", distance=0.1)
    hallucinated_id = uuid.uuid4()
    workflow = AnswerQueryWorkflow(
        corpus_repository=_FakeCorpusRepository([passage]),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=_FakeGenerationProvider(cited_passage_ids=[hallucinated_id]),
        query_repository=_FakeQueryRepository(),
    )

    answer = workflow.answer_query(
        workspace_id=uuid.uuid4(),
        query_text="How do I treat varroa?",
        jurisdiction_id=uuid.uuid4(),
    )

    assert answer.grounding_status == "ungrounded"
    assert answer.citations == []
