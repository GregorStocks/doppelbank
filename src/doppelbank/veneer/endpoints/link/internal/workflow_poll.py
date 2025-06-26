from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest

from .workflow_shared import WorkflowResponse, WorkflowState

router = APIRouter()


class WorkflowPollRequest(VeneerRequest):
    continuation_token: str | None = None


@router.post("/link/workflow/poll")
async def workflow_poll(request: WorkflowPollRequest) -> WorkflowResponse:
    return WorkflowState.create_response(
        "todo", continuation_token=request.continuation_token
    )
