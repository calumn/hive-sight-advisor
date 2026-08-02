from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from hive_sight_advisor_api.repositories.corpus_repository import Passage


@dataclass(frozen=True)
class GeneratedAnswer:
    text: str
    cited_passage_ids: list[UUID]


class GenerationProvider(Protocol):
    def generate_answer(self, query_text: str, passages: list[Passage]) -> GeneratedAnswer: ...
