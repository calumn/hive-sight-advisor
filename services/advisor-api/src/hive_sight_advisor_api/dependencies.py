from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import Depends, Header, HTTPException

from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider
from hive_sight_advisor_api.adapters.generation_claude import ClaudeGenerationProvider
from hive_sight_advisor_api.adapters.generation_provider import GenerationProvider
from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository
from hive_sight_advisor_api.repositories.query_repository import PostgresQueryRepository
from hive_sight_advisor_api.settings import Settings, load_settings
from hive_sight_advisor_api.workflows.answer_query import AnswerQueryWorkflow


@lru_cache
def get_settings() -> Settings:
    return load_settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_db_connection(settings: SettingsDep) -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(settings.database_url)
    try:
        yield connection
    finally:
        connection.close()


DbConnectionDep = Annotated[psycopg.Connection, Depends(get_db_connection)]


def get_corpus_repository(connection: DbConnectionDep) -> CorpusRepository:
    return CorpusRepository(connection)


CorpusRepositoryDep = Annotated[CorpusRepository, Depends(get_corpus_repository)]


def get_query_repository(connection: DbConnectionDep) -> PostgresQueryRepository:
    return PostgresQueryRepository(connection)


QueryRepositoryDep = Annotated[PostgresQueryRepository, Depends(get_query_repository)]


def get_embedding_provider(settings: SettingsDep) -> EmbeddingProvider:
    if settings.voyage_api_key:
        return VoyageEmbeddingProvider(api_key=settings.voyage_api_key)
    return StubEmbeddingProvider()


EmbeddingProviderDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]


def get_generation_provider(settings: SettingsDep) -> GenerationProvider:
    if settings.anthropic_api_key:
        return ClaudeGenerationProvider(api_key=settings.anthropic_api_key)
    return StubGenerationProvider()


GenerationProviderDep = Annotated[GenerationProvider, Depends(get_generation_provider)]


def get_answer_query_workflow(
    corpus_repository: CorpusRepositoryDep,
    embedding_provider: EmbeddingProviderDep,
    generation_provider: GenerationProviderDep,
    query_repository: QueryRepositoryDep,
) -> AnswerQueryWorkflow:
    return AnswerQueryWorkflow(
        corpus_repository=corpus_repository,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        query_repository=query_repository,
    )


AnswerQueryWorkflowDep = Annotated[AnswerQueryWorkflow, Depends(get_answer_query_workflow)]


def get_dev_user_id(
    x_dev_user_id: Annotated[str | None, Header(alias="x-dev-user-id")] = None,
) -> UUID:
    if x_dev_user_id is None:
        raise HTTPException(status_code=401, detail="Missing dev-auth header.")
    try:
        return UUID(x_dev_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid dev-auth header.") from exc


DevUserIdDep = Annotated[UUID, Depends(get_dev_user_id)]
