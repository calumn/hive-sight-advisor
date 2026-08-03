from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hive_sight_advisor_api.dependencies import (
    AnswerQueryWorkflowDep,
    DevUserIdDep,
    QueryRepositoryDep,
)

router = APIRouter()


class QueryRequest(BaseModel):
    workspace_id: UUID
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
    dev_user_id: DevUserIdDep,
    query_repository: QueryRepositoryDep,
    workflow: AnswerQueryWorkflowDep,
) -> AnswerResponse:
    if not query_repository.has_active_membership(dev_user_id, request.workspace_id):
        raise HTTPException(status_code=403, detail="No active Workspace Membership.")

    answer = workflow.answer_query(
        workspace_id=request.workspace_id,
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
