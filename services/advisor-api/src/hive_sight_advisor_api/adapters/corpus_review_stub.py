from hive_sight_advisor_api.repositories.corpus_repository import Passage


class StubCorpusReviewProvider:
    def review_candidate(
        self,
        candidate_text: str,
        jurisdiction_display_name: str,
        nearby_passages: list[Passage],
    ) -> str:
        return (
            f"Stub review for {jurisdiction_display_name}: found {len(nearby_passages)} nearby "
            f"passage(s) to compare against."
        )
