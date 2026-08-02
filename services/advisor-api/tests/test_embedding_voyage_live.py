import os

import pytest

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS
from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider


@pytest.mark.skipif(
    not os.getenv("VOYAGE_API_KEY"),
    reason="Set VOYAGE_API_KEY to run the live Voyage AI embedding contract test.",
)
def test_voyage_embedding_returns_correct_dimension() -> None:
    provider = VoyageEmbeddingProvider(api_key=os.environ["VOYAGE_API_KEY"])

    embedding = provider.embed("varroa mite treatment")

    assert len(embedding) == EMBEDDING_DIMENSIONS
    assert any(value != 0.0 for value in embedding)
