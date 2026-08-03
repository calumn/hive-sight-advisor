import os
import uuid

import pytest

from hive_sight_advisor_api.adapters.corpus_review_claude import ClaudeCorpusReviewProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Set ANTHROPIC_API_KEY to run the live Claude corpus review contract test.",
)
def test_claude_review_flags_an_unrelated_candidate_document() -> None:
    provider = ClaudeCorpusReviewProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    nearby_passage = Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content="Varroa mites are treated with an oxalic acid vaporization protocol.",
        distance=0.7,
        document_title="Managing Varroa: A Guide for UK Beekeepers",
        document_source="APHA BeeBase",
        document_source_url="https://www.nationalbeeunit.com/",
        document_licence_terms="Open Government Licence",
        document_status="active",
        superseded_by_document_title=None,
    )

    advisory = provider.review_candidate(
        candidate_text="A recipe for lemon drizzle cake, including baking time and temperature.",
        jurisdiction_display_name="United Kingdom",
        nearby_passages=[nearby_passage],
    )

    assert len(advisory) > 0
