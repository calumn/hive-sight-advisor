import uuid

from hive_sight_advisor_api.adapters.corpus_review_stub import StubCorpusReviewProvider
from hive_sight_advisor_api.repositories.corpus_repository import Passage


def _passage(text_content: str) -> Passage:
    return Passage(
        id=uuid.uuid4(),
        corpus_document_id=uuid.uuid4(),
        text_content=text_content,
        distance=0.2,
        document_title="Existing Document",
        document_source="Some Source",
        document_source_url=None,
        document_licence_terms="Some Licence",
        document_status="active",
        superseded_by_document_title=None,
    )


def test_review_candidate_mentions_jurisdiction_and_zero_nearby_passages() -> None:
    provider = StubCorpusReviewProvider()

    advisory = provider.review_candidate(
        candidate_text="A new Varroa treatment document.",
        jurisdiction_display_name="United Kingdom",
        nearby_passages=[],
    )

    assert "United Kingdom" in advisory
    assert "0 nearby" in advisory


def test_review_candidate_reports_the_count_of_nearby_passages() -> None:
    provider = StubCorpusReviewProvider()
    passages = [_passage("Existing passage one."), _passage("Existing passage two.")]

    advisory = provider.review_candidate(
        candidate_text="A new Varroa treatment document.",
        jurisdiction_display_name="United States",
        nearby_passages=passages,
    )

    assert "United States" in advisory
    assert "2 nearby" in advisory
