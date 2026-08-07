import json
import uuid
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from hive_sight_advisor_api.adapters.generation_claude import (
    ClaudeGenerationProvider,
    TruncatedGenerationError,
)
from hive_sight_advisor_api.repositories.corpus_repository import Passage


def _passage() -> Passage:
    return Passage(
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


@dataclass
class _FakeResponse:
    stop_reason: str
    text: str

    @property
    def content(self):
        return [SimpleNamespace(type="text", text=self.text)]


class _FakeMessages:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def create(self, **kwargs):
        return self._response


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.messages = _FakeMessages(response)


def test_generate_answer_parses_a_complete_response() -> None:
    payload = json.dumps({"answer": "Use oxalic acid.", "cited_passage_ids": []})
    client = _FakeClient(_FakeResponse(stop_reason="end_turn", text=payload))
    provider = ClaudeGenerationProvider(api_key="unused", client=client)

    result = provider.generate_answer("How do I treat varroa?", [_passage()])

    assert result.text == "Use oxalic acid."


def test_generate_answer_raises_a_clear_error_when_the_response_was_truncated() -> None:
    truncated_json = '{"answer": "Use oxalic acid vaporisation, and also compare it with'
    client = _FakeClient(_FakeResponse(stop_reason="max_tokens", text=truncated_json))
    provider = ClaudeGenerationProvider(api_key="unused", client=client)

    with pytest.raises(TruncatedGenerationError):
        provider.generate_answer("How do I treat varroa?", [_passage()])
