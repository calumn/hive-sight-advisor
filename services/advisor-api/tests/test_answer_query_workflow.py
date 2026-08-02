import uuid

from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage
from hive_sight_advisor_api.workflows.answer_query import AnswerQueryWorkflow


class _FakeCorpusRepository:
    def __init__(self, passages: list[Passage]) -> None:
        self._passages = passages

    def find_similar_passages(self, query_embedding, jurisdiction_id, limit=1):
        return self._passages[:limit]


class _FakeQueryRepository:
    def __init__(self) -> None:
        self.saved = None

    def save(self, workspace_id, query_id, query_text, jurisdiction_id, answer):
        self.saved = (workspace_id, query_id, query_text, jurisdiction_id, answer)


def test_answer_query_orchestrates_embed_retrieve_generate_and_persist() -> None:
    passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
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
