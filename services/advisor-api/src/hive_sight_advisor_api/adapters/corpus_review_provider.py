from __future__ import annotations

from typing import Protocol

from hive_sight_advisor_api.repositories.corpus_repository import Passage


class CorpusReviewProvider(Protocol):
    def review_candidate(
        self,
        candidate_text: str,
        jurisdiction_display_name: str,
        nearby_passages: list[Passage],
    ) -> str: ...
