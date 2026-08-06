import tenacity
import voyageai
from voyageai.error import (
    APIConnectionError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
    TryAgain,
)

from hive_sight_advisor_api.adapters.embedding_provider import EMBEDDING_DIMENSIONS

# Transient errors worth retrying. Deliberately excludes AuthenticationError,
# InvalidRequestError, and MalformedRequestError — retrying those can't succeed and
# would only delay a failure that needs a human to fix, not a retry to paper over.
RETRYABLE_ERRORS = (RateLimitError, ServiceUnavailableError, Timeout, APIConnectionError, TryAgain)


class VoyageEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "voyage-3-large",
        client: voyageai.Client | None = None,
        wait: tenacity.wait.wait_base | None = None,
    ) -> None:
        self._client = client if client is not None else voyageai.Client(api_key=api_key)
        self._model = model
        self._retrying = tenacity.Retrying(
            stop=tenacity.stop_after_attempt(4),
            wait=wait if wait is not None else tenacity.wait_exponential_jitter(initial=1, max=8),
            retry=tenacity.retry_if_exception_type(RETRYABLE_ERRORS),
            reraise=True,
        )

    def embed(self, text: str) -> list[float]:
        result = self._retrying(
            self._client.embed,
            [text],
            model=self._model,
            input_type="query",
            output_dimension=EMBEDDING_DIMENSIONS,
        )
        return result.embeddings[0]
