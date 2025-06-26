import uuid

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()


class WorkflowPollRequest(VeneerRequest):
    workflow_session_id: str


class WorkflowPollResponse(VeneerResponse):
    oauth_redirect_complete: dict[str, bool]
    request_id: str
    workflow_session_id: str


@router.post("/link/workflow/poll")
async def workflow_poll(request: WorkflowPollRequest) -> WorkflowPollResponse:
    return WorkflowPollResponse(
        oauth_redirect_complete={"is_complete": True},
        request_id=str(uuid.uuid4()),
        workflow_session_id=request.workflow_session_id,
    )
