from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hive_sight_advisor_api.dependencies import (
    CorrectionRepositoryDep,
    DevUserIdDep,
    QueryRepositoryDep,
)

router = APIRouter()


class CorrectionRequest(BaseModel):
    workspace_id: UUID
    answer_id: UUID
    notes: str = Field(min_length=1)


class CorrectionResponse(BaseModel):
    id: UUID
    answer_id: UUID
    status: str


@router.post("/corrections", response_model=CorrectionResponse)
def submit_correction(
    request: CorrectionRequest,
    dev_user_id: DevUserIdDep,
    query_repository: QueryRepositoryDep,
    correction_repository: CorrectionRepositoryDep,
) -> CorrectionResponse:
    if not query_repository.has_active_membership(dev_user_id, request.workspace_id):
        raise HTTPException(status_code=403, detail="No active Workspace Membership.")

    if not correction_repository.answer_belongs_to_workspace(
        request.answer_id, request.workspace_id
    ):
        raise HTTPException(status_code=404, detail="Answer not found in this Workspace.")

    correction = correction_repository.save(
        workspace_id=request.workspace_id,
        answer_id=request.answer_id,
        created_by_user_id=dev_user_id,
        notes=request.notes,
    )

    return CorrectionResponse(
        id=correction.id, answer_id=correction.answer_id, status=correction.status
    )
