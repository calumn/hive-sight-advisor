import json
from uuid import UUID

import anthropic

from hive_sight_advisor_api.adapters.generation_provider import GeneratedAnswer
from hive_sight_advisor_api.repositories.corpus_repository import Passage

_SYSTEM_PROMPT = (
    "You are a beekeeping advisor. Answer the beekeeper's question using ONLY the "
    "grounding passages provided below. Do not use knowledge beyond what the passages "
    "state. Every claim in your answer must be traceable to at least one passage. "
    "Cite every passage id you relied on."
)

_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "cited_passage_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "cited_passage_ids"],
    "additionalProperties": False,
}


class ClaudeGenerationProvider:
    def __init__(self, api_key: str, model: str = "claude-opus-5") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate_answer(self, query_text: str, passages: list[Passage]) -> GeneratedAnswer:
        grounding = "\n\n".join(
            f"[Passage {passage.id}]\n{passage.text_content}" for passage in passages
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": _ANSWER_SCHEMA},
            },
            messages=[
                {
                    "role": "user",
                    "content": f"Grounding passages:\n\n{grounding}\n\nQuestion: {query_text}",
                }
            ],
        )
        text_block = next(block for block in response.content if block.type == "text")
        payload = json.loads(text_block.text)
        return GeneratedAnswer(
            text=payload["answer"],
            cited_passage_ids=[UUID(passage_id) for passage_id in payload["cited_passage_ids"]],
        )
