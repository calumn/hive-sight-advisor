from hive_sight_advisor_api.adapters.generation_provider import GeneratedAnswer
from hive_sight_advisor_api.repositories.corpus_repository import Passage


class StubGenerationProvider:
    def generate_answer(self, query_text: str, passages: list[Passage]) -> GeneratedAnswer:
        excerpts = " ".join(passage.text_content for passage in passages)
        return GeneratedAnswer(
            text=f"Based on the retrieved guidance: {excerpts}",
            cited_passage_ids=[passage.id for passage in passages],
        )
