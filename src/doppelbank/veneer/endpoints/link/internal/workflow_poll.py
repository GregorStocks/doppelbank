from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest
from doppelbank.veneer.endpoints.link.internal.models import WorkflowResponse
from doppelbank.veneer.endpoints.link.internal.states import account_select

router = APIRouter()


class WorkflowPollRequest(VeneerRequest):
    continuation_token: str | None = None


@router.post("/link/workflow/poll")
async def workflow_poll(_request: WorkflowPollRequest) -> WorkflowResponse:
    return account_select.create_account_select_response()
