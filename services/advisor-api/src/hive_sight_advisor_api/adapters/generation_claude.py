import json
from uuid import UUID

import anthropic

from hive_sight_advisor_api.adapters.generation_provider import GeneratedAnswer
from hive_sight_advisor_api.repositories.corpus_repository import Passage

_SYSTEM_PROMPT = (
    "You are a beekeeping advisor. Answer the beekeeper's question using ONLY the "
    "grounding passages provided below. Do not use knowledge beyond what the passages "
    "state. Every claim in your answer must be traceable to at least one passage. "
    "Record every passage id you relied on in the cited_passage_ids field ONLY. "
    "The answer field is shown directly to the beekeeper as plain prose — never include "
    "a passage id, bracketed reference, or any other citation marker inside it; the "
    "citation list is rendered separately from cited_passage_ids, so the answer text "
    "should read naturally on its own, with no visible trace of the underlying passage "
    "identifiers. "
    "You may be given more than one passage. If more than one describes a genuinely "
    "relevant but different treatment option, compare them explicitly rather than "
    "silently picking one — call out real differences such as temperature constraints, "
    "organic-certification compatibility, and treatment duration where the passages "
    "describe them. If only one passage is actually relevant to the question, just "
    "answer normally; do not force a comparison where there isn't a genuine choice."
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


class TruncatedGenerationError(Exception):
    """Claude's response hit max_tokens before completing its structured output."""


class ClaudeGenerationProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-5",
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self._client = client if client is not None else anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate_answer(self, query_text: str, passages: list[Passage]) -> GeneratedAnswer:
        grounding = "\n\n".join(
            f"[Passage {passage.id}]\n{passage.text_content}" for passage in passages
        )
        response = self._client.messages.create(
            model=self._model,
            # Passages retrieved for comparison (up to 5, Slice 0007) can push a
            # thorough multi-option comparison well past a short budget - 1024 was
            # observed truncating a real 5-passage response mid-JSON.
            max_tokens=4096,
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
        if response.stop_reason == "max_tokens":
            raise TruncatedGenerationError(
                "Claude's response was truncated at the token limit before completing "
                "its structured output."
            )
        text_block = next(block for block in response.content if block.type == "text")
        payload = json.loads(text_block.text)
        return GeneratedAnswer(
            text=payload["answer"],
            cited_passage_ids=[UUID(passage_id) for passage_id in payload["cited_passage_ids"]],
        )
