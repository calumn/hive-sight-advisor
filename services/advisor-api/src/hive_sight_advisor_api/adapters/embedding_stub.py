import hashlib

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS


class StubEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[index % len(digest)] / 255.0 for index in range(EMBEDDING_DIMENSIONS)]
