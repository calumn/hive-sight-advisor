from __future__ import annotations

from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.db import test_database_url
from hive_sight_advisor_api.settings import load_settings
from seed_slice_0001 import seed


def main() -> None:
    settings = load_settings()
    seed(test_database_url(settings.database_url), StubEmbeddingProvider())


if __name__ == "__main__":
    main()
