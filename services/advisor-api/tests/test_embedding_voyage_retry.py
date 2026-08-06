import pytest
import tenacity
from voyageai.error import AuthenticationError, RateLimitError

from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider


class _FakeEmbedResult:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = embeddings


class _FailThenSucceedClient:
    def __init__(self, exception: Exception, fail_times: int) -> None:
        self._exception = exception
        self._fail_times = fail_times
        self.call_count = 0

    def embed(self, texts, model, input_type, output_dimension):
        self.call_count += 1
        if self.call_count <= self._fail_times:
            raise self._exception
        return _FakeEmbedResult(embeddings=[[0.1] * output_dimension])


class _AlwaysFailClient:
    def __init__(self, exception: Exception) -> None:
        self._exception = exception
        self.call_count = 0

    def embed(self, texts, model, input_type, output_dimension):
        self.call_count += 1
        raise self._exception


def test_embed_retries_on_a_transient_error_then_succeeds() -> None:
    client = _FailThenSucceedClient(RateLimitError("rate limited"), fail_times=2)
    provider = VoyageEmbeddingProvider(api_key="test", client=client, wait=tenacity.wait_none())

    result = provider.embed("How do I treat varroa?")

    assert len(result) == 1024
    assert client.call_count == 3


def test_embed_gives_up_after_max_attempts() -> None:
    client = _AlwaysFailClient(RateLimitError("rate limited"))
    provider = VoyageEmbeddingProvider(api_key="test", client=client, wait=tenacity.wait_none())

    with pytest.raises(RateLimitError):
        provider.embed("How do I treat varroa?")

    assert client.call_count == 4


def test_embed_does_not_retry_a_non_retryable_error() -> None:
    client = _AlwaysFailClient(AuthenticationError("bad key"))
    provider = VoyageEmbeddingProvider(api_key="test", client=client, wait=tenacity.wait_none())

    with pytest.raises(AuthenticationError):
        provider.embed("How do I treat varroa?")

    assert client.call_count == 1
