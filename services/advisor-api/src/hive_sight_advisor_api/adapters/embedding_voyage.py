import voyageai

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS


class VoyageEmbeddingProvider:
    def __init__(self, api_key: str, model: str = "voyage-3-large") -> None:
        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    def embed(self, text: str) -> list[float]:
        result = self._client.embed(
            [text],
            model=self._model,
            input_type="query",
            output_dimension=EMBEDDING_DIMENSIONS,
        )
        return result.embeddings[0]
