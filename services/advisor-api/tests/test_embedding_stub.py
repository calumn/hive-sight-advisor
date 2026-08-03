import math

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS
from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))
    return 1 - dot / (magnitude_a * magnitude_b)


def test_stub_embedding_is_deterministic_and_correct_dimension() -> None:
    provider = StubEmbeddingProvider()

    first = provider.embed("varroa mite treatment")
    second = provider.embed("varroa mite treatment")
    different = provider.embed("bee foraging behaviour")

    assert first == second
    assert len(first) == EMBEDDING_DIMENSIONS
    assert first != different


def test_stub_embedding_distance_reflects_shared_vocabulary() -> None:
    # The retrieval seam's grounding classification depends on distance actually
    # meaning something. A pure content hash gives an essentially random distance
    # for any two different strings, so a single close/far pair can pass this
    # assertion by chance alone. Comparing every related pair against every
    # unrelated pair makes a lucky coincidence astronomically unlikely, while a
    # real word-overlap-aware embedding satisfies it reliably.
    provider = StubEmbeddingProvider()

    passage = provider.embed(
        "Varroa mites are treated with oxalic acid vaporisation applied in late autumn."
    )
    related_texts = [
        "Oxalic acid vaporisation treats varroa mites, applied in late autumn.",
        "Late autumn oxalic acid vaporisation is used to treat varroa mites.",
        "Varroa mites are treated with oxalic acid vaporisation in autumn.",
    ]
    unrelated_texts = [
        "What is the capital of France?",
        "The quarterly sales report is due on Friday.",
        "My favourite recipe uses fresh basil and garlic.",
    ]

    related_distances = [_cosine_distance(passage, provider.embed(text)) for text in related_texts]
    unrelated_distances = [_cosine_distance(passage, provider.embed(text)) for text in unrelated_texts]

    assert max(related_distances) < min(unrelated_distances)
