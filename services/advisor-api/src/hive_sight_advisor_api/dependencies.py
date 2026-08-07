from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

import psycopg
from fastapi import Depends, Header, HTTPException, Request
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
from hive_sight_advisor_api.google_sign_in import GoogleIdTokenVerifier, InvalidGoogleIdToken
from hive_sight_advisor_api.rate_limiter import InMemoryRateLimiter, RateLimiter
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository
from hive_sight_advisor_api.repositories.correction_repository import CorrectionRepository
from hive_sight_advisor_api.repositories.jurisdiction_repository import JurisdictionRepository
from hive_sight_advisor_api.repositories.proposed_treatment_repository import (
    ProposedTreatmentRepository,
)
from hive_sight_advisor_api.repositories.query_repository import PostgresQueryRepository
from hive_sight_advisor_api.repositories.user_provisioning_repository import (
    ProvisionedIdentity,
    UserProvisioningRepository,
)
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


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


ClientIpDep = Annotated[str, Depends(get_client_ip)]


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = load_settings()
    return InMemoryRateLimiter(
        limit=settings.guest_rate_limit,
        window_seconds=settings.guest_rate_limit_window_seconds,
    )


RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


@lru_cache
def get_google_id_token_verifier() -> GoogleIdTokenVerifier:
    settings = load_settings()
    return GoogleIdTokenVerifier(client_id=settings.google_client_id)


GoogleIdTokenVerifierDep = Annotated[GoogleIdTokenVerifier, Depends(get_google_id_token_verifier)]


def get_user_provisioning_repository(connection: DbConnectionDep) -> UserProvisioningRepository:
    return UserProvisioningRepository(connection)


UserProvisioningRepositoryDep = Annotated[
    UserProvisioningRepository, Depends(get_user_provisioning_repository)
]


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _verify_and_provision(
    token: str,
    verifier: GoogleIdTokenVerifier,
    provisioning: UserProvisioningRepository,
) -> ProvisionedIdentity:
    try:
        identity = verifier.verify(token)
    except InvalidGoogleIdToken as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired sign-in.") from exc
    return provisioning.find_or_provision(
        google_sub=identity.sub, email=identity.email, display_name=identity.name
    )


def get_required_identity(
    verifier: GoogleIdTokenVerifierDep,
    provisioning: UserProvisioningRepositoryDep,
    authorization: Annotated[str | None, Header()] = None,
) -> ProvisionedIdentity:
    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Sign in required.")
    return _verify_and_provision(token, verifier, provisioning)


RequiredIdentityDep = Annotated[ProvisionedIdentity, Depends(get_required_identity)]


def get_optional_identity(
    verifier: GoogleIdTokenVerifierDep,
    provisioning: UserProvisioningRepositoryDep,
    authorization: Annotated[str | None, Header()] = None,
) -> ProvisionedIdentity | None:
    token = _extract_bearer_token(authorization)
    if token is None:
        return None
    return _verify_and_provision(token, verifier, provisioning)


OptionalIdentityDep = Annotated[ProvisionedIdentity | None, Depends(get_optional_identity)]


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
