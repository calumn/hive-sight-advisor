import anthropic

from hive_sight_advisor_api.repositories.corpus_repository import Passage

_SYSTEM_PROMPT = (
    "You are assisting a Corpus Curator who is deciding whether to add a candidate document to "
    "a beekeeping knowledge base for a specific jurisdiction. Assess two things only: (1) whether "
    "the candidate text is relevant to Varroa mite management and appropriate for the stated "
    "jurisdiction, and (2) whether it appears to overlap with or contradict any of the existing "
    "passages shown below. Do not judge the factual or scientific accuracy of any treatment "
    "claims — the Curator is the domain expert for that. Give a brief advisory summary. You are "
    "not making the final decision; the Curator retains that."
)


class ClaudeCorpusReviewProvider:
    def __init__(self, api_key: str, model: str = "claude-opus-5") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def review_candidate(
        self,
        candidate_text: str,
        jurisdiction_display_name: str,
        nearby_passages: list[Passage],
    ) -> str:
        if nearby_passages:
            nearby = "\n\n".join(
                f"[Existing passage from \"{passage.document_title}\"]\n{passage.text_content}"
                for passage in nearby_passages
            )
        else:
            nearby = "(No existing passages found for this jurisdiction.)"

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Jurisdiction: {jurisdiction_display_name}\n\n"
                        f"Candidate document text:\n{candidate_text}\n\n"
                        f"Nearby existing passages:\n{nearby}"
                    ),
                }
            ],
        )
        text_block = next(block for block in response.content if block.type == "text")
        return text_block.text
