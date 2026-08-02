from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS
from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider


def test_stub_embedding_is_deterministic_and_correct_dimension() -> None:
    provider = StubEmbeddingProvider()

    first = provider.embed("varroa mite treatment")
    second = provider.embed("varroa mite treatment")
    different = provider.embed("bee foraging behaviour")

    assert first == second
    assert len(first) == EMBEDDING_DIMENSIONS
    assert first != different
