from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hive_sight_advisor_api.dependencies import HiveSightServiceAuthDep, TreatmentPlanWorkflowDep
from hive_sight_advisor_api.routers.query import CitationResponse

router = APIRouter(prefix="/integrations/hivesight")


class TreatmentPlanRequest(BaseModel):
    hive_id: str
    jurisdiction_id: UUID
    situational_context: str


class TreatmentPlanResponse(BaseModel):
    text: str
    grounding_status: str
    citations: list[CitationResponse]


@router.post("/treatment-plans", response_model=TreatmentPlanResponse)
def request_treatment_plan(
    request: TreatmentPlanRequest,
    _hivesight_service_credential: HiveSightServiceAuthDep,
    workflow: TreatmentPlanWorkflowDep,
) -> TreatmentPlanResponse:
    answer = workflow.request_treatment_plan(
        hive_id=request.hive_id,
        jurisdiction_id=request.jurisdiction_id,
        query_text=request.situational_context,
    )
    return TreatmentPlanResponse(
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


class TreatmentCompletionRequest(BaseModel):
    hive_id: str


class ProposedTreatmentResponse(BaseModel):
    id: UUID
    status: str


@router.post("/treatment-plans/completions", response_model=ProposedTreatmentResponse)
def confirm_treatment_completed(
    request: TreatmentCompletionRequest,
    _hivesight_service_credential: HiveSightServiceAuthDep,
    workflow: TreatmentPlanWorkflowDep,
) -> ProposedTreatmentResponse:
    completed = workflow.confirm_completed(request.hive_id)
    if completed is None:
        raise HTTPException(
            status_code=404, detail="No suggested treatment awaiting completion for that hive."
        )
    return ProposedTreatmentResponse(id=completed.id, status=completed.status)
