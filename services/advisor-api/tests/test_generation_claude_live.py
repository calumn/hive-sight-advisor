import os
import re
import uuid

import pytest

from hive_sight_advisor_api.adapters.generation_claude import ClaudeGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage

_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


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
        distance=0.1,
        document_title="Managing Varroa: A Guide for UK Beekeepers",
        document_source="APHA BeeBase",
        document_source_url="https://www.nationalbeeunit.com/",
        document_licence_terms="Open Government Licence",
        document_status="active",
        superseded_by_document_title=None,
    )

    result = provider.generate_answer("How do I treat varroa mites?", [passage])

    assert "oxalic acid" in result.text.lower()
    assert result.cited_passage_ids == [passage.id]
    assert not _UUID_PATTERN.search(result.text), (
        "Answer text should read as plain prose with no raw passage id leaking in - "
        "citations belong in cited_passage_ids only."
    )


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Set ANTHROPIC_API_KEY to run the live Claude generation contract test.",
)
def test_claude_generation_compares_genuinely_different_treatment_options() -> None:
    provider = ClaudeGenerationProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    amitraz_passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content=(
            "Apivar is a UK-authorised Varroa treatment using amitraz-impregnated strips. "
            "It has no temperature restriction and can be used at any time of year. Amitraz "
            "is a synthetic acaricide and is not compatible with organic certification "
            "standards."
        ),
        distance=0.2,
        document_title="Apivar (Amitraz) Varroa Treatment",
        document_source="Thorne (Beehives) Ltd",
        document_source_url="https://www.thorne.co.uk/",
        document_licence_terms="All rights reserved (retailer product literature)",
        document_status="active",
        superseded_by_document_title=None,
    )
    thymol_passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content=(
            "Apiguard is a UK-authorised Varroa treatment based on thymol. It works best "
            "when daytime temperatures reach at least fifteen degrees Celsius. Because "
            "thymol is plant-derived, Apiguard is compatible with organic certification "
            "standards."
        ),
        distance=0.2,
        document_title="Apiguard (Thymol) Varroa Treatment",
        document_source="Vita Bee Health",
        document_source_url="https://www.vita-europe.com/",
        document_licence_terms="All rights reserved (manufacturer product literature)",
        document_status="active",
        superseded_by_document_title=None,
    )

    result = provider.generate_answer(
        "What are my options for treating varroa, and how do they compare?",
        [amitraz_passage, thymol_passage],
    )

    assert "apivar" in result.text.lower() or "amitraz" in result.text.lower()
    assert "apiguard" in result.text.lower() or "thymol" in result.text.lower()
    assert set(result.cited_passage_ids) == {amitraz_passage.id, thymol_passage.id}
    assert not _UUID_PATTERN.search(result.text), (
        "Answer text should read as plain prose with no raw passage id leaking in - "
        "citations belong in cited_passage_ids only."
    )
