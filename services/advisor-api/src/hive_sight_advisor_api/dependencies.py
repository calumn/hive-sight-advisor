from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import Depends, Header, HTTPException
from langgraph.checkpoint.postgres import PostgresSaver

from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider
from hive_sight_advisor_api.adapters.generation_claude import ClaudeGenerationProvider
from hive_sight_advisor_api.adapters.generation_provider import GenerationProvider
from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.adapters.treatment_suggestion_provider import (
    TreatmentSuggestionProvider,
)
from hive_sight_advisor_api.adapters.treatment_suggestion_stub import (
    StubTreatmentSuggestionProvider,
)
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository
from hive_sight_advisor_api.repositories.correction_repository import CorrectionRepository
from hive_sight_advisor_api.repositories.jurisdiction_repository import JurisdictionRepository
from hive_sight_advisor_api.repositories.proposed_treatment_repository import (
    ProposedTreatmentRepository,
)
from hive_sight_advisor_api.repositories.query_repository import PostgresQueryRepository
from hive_sight_advisor_api.settings import Settings, load_settings
from hive_sight_advisor_api.workflows.answer_query import AnswerQueryWorkflow
from hive_sight_advisor_api.workflows.treatment_plan_workflow import TreatmentPlanWorkflow


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


def get_correction_repository(connection: DbConnectionDep) -> CorrectionRepository:
    return CorrectionRepository(connection)


CorrectionRepositoryDep = Annotated[CorrectionRepository, Depends(get_correction_repository)]


def get_jurisdiction_repository(connection: DbConnectionDep) -> JurisdictionRepository:
    return JurisdictionRepository(connection)


JurisdictionRepositoryDep = Annotated[JurisdictionRepository, Depends(get_jurisdiction_repository)]


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
    settings: SettingsDep,
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
        grounded_distance_threshold=settings.grounded_distance_threshold,
        partial_distance_threshold=settings.partial_distance_threshold,
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


def get_hivesight_service_credential(
    settings: SettingsDep,
    x_hivesight_service_key: Annotated[str | None, Header(alias="x-hivesight-service-key")] = None,
) -> None:
    if not settings.hivesight_service_key or x_hivesight_service_key != settings.hivesight_service_key:
        raise HTTPException(status_code=401, detail="Invalid or missing HiveSight service credential.")


HiveSightServiceAuthDep = Annotated[None, Depends(get_hivesight_service_credential)]


def get_proposed_treatment_repository(connection: DbConnectionDep) -> ProposedTreatmentRepository:
    return ProposedTreatmentRepository(connection)


ProposedTreatmentRepositoryDep = Annotated[
    ProposedTreatmentRepository, Depends(get_proposed_treatment_repository)
]


def get_treatment_suggestion_provider() -> TreatmentSuggestionProvider:
    # No live HiveSight endpoint exists yet to call — see the
    # hivesight-advisor-integration-contract skill for current status.
    return StubTreatmentSuggestionProvider()


TreatmentSuggestionProviderDep = Annotated[
    TreatmentSuggestionProvider, Depends(get_treatment_suggestion_provider)
]


def get_checkpointer(settings: SettingsDep) -> Iterator[PostgresSaver]:
    with PostgresSaver.from_conn_string(settings.database_url) as saver:
        yield saver


CheckpointerDep = Annotated[PostgresSaver, Depends(get_checkpointer)]


def get_treatment_plan_workflow(
    answer_query_workflow: AnswerQueryWorkflowDep,
    treatment_suggestion_provider: TreatmentSuggestionProviderDep,
    proposed_treatment_repository: ProposedTreatmentRepositoryDep,
    checkpointer: CheckpointerDep,
) -> TreatmentPlanWorkflow:
    return TreatmentPlanWorkflow(
        answer_query_workflow=answer_query_workflow,
        treatment_suggestion_provider=treatment_suggestion_provider,
        proposed_treatment_repository=proposed_treatment_repository,
        checkpointer=checkpointer,
    )


TreatmentPlanWorkflowDep = Annotated[TreatmentPlanWorkflow, Depends(get_treatment_plan_workflow)]
