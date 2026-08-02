from typing import Protocol

EMBEDDING_DIMENSIONS = 1024


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...
