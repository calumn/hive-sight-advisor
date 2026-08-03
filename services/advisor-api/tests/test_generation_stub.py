import uuid

from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage


def test_stub_generation_cites_the_provided_passages() -> None:
    provider = StubGenerationProvider()
    passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
        distance=0.1,
    )

    result = provider.generate_answer("How do I treat varroa?", [passage])

    assert passage.text_content in result.text
    assert result.cited_passage_ids == [passage.id]
