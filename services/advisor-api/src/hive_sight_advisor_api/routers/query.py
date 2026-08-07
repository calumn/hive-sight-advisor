from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hive_sight_advisor_api.dependencies import (
    AnswerQueryWorkflowDep,
    ClientIpDep,
    RateLimiterDep,
)
from hive_sight_advisor_api.guest import GUEST_WORKSPACE_ID

router = APIRouter()


class QueryRequest(BaseModel):
    jurisdiction_id: UUID
    text: str


class CitationResponse(BaseModel):
    passage_id: UUID
    document_title: str
    document_source: str
    document_source_url: str | None
    document_licence_terms: str
    is_superseded: bool
    superseded_by_document_title: str | None


class AnswerResponse(BaseModel):
    id: UUID
    query_id: UUID
    text: str
    grounding_status: str
    citations: list[CitationResponse]


@router.post("/queries", response_model=AnswerResponse)
def submit_query(
    request: QueryRequest,
    client_ip: ClientIpDep,
    rate_limiter: RateLimiterDep,
    workflow: AnswerQueryWorkflowDep,
) -> AnswerResponse:
    if not rate_limiter.allow(client_ip):
        raise HTTPException(
            status_code=429,
            detail={
                "reason": "guest_rate_limit_exceeded",
                "message": "Guest query limit reached for this hour. Sign in for higher limits.",
            },
        )

    answer = workflow.answer_query(
        workspace_id=GUEST_WORKSPACE_ID,
        query_text=request.text,
        jurisdiction_id=request.jurisdiction_id,
    )

    return AnswerResponse(
        id=answer.id,
        query_id=answer.query_id,
        text=answer.text,
        grounding_status=answer.grounding_status,
        citations=[
            CitationResponse(
                passage_id=citation.passage_id,
                document_title=citation.document_title,
                document_source=citation.document_source,
                document_source_url=citation.document_source_url,
                document_licence_terms=citation.document_licence_terms,
                is_superseded=citation.is_superseded,
                superseded_by_document_title=citation.superseded_by_document_title,
            )
            for citation in answer.citations
        ],
    )
