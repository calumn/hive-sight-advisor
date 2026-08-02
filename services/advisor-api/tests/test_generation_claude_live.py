import os
import uuid

import pytest

from hive_sight_advisor_api.adapters.generation_claude import ClaudeGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Set ANTHROPIC_API_KEY to run the live Claude generation contract test.",
)
def test_claude_generation_grounds_answer_in_the_passage_and_cites_it() -> None:
    provider = ClaudeGenerationProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
    )

    result = provider.generate_answer("How do I treat varroa mites?", [passage])

    assert "oxalic acid" in result.text.lower()
    assert result.cited_passage_ids == [passage.id]
