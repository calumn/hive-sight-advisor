import hashlib
import math
import re

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS

_WORD_PATTERN = re.compile(r"[a-z0-9]+")


class StubEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        for word in _WORD_PATTERN.findall(text.lower()):
            dimension = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIMENSIONS
            vector[dimension] += 1.0

        magnitude = math.sqrt(sum(component * component for component in vector))
        if magnitude == 0.0:
            return vector
        return [component / magnitude for component in vector]
