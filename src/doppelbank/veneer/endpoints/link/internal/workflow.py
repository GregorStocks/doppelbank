import logging

from fastapi import APIRouter

from doppelbank.veneer.endpoints.link.internal.models import (
    LinkWorkflowStartRequest,
    WorkflowNextRequest,
    WorkflowResponse,
)
from doppelbank.veneer.endpoints.link.internal.states import (
    account_select,
    account_select_success,
    done,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/link/workflow/start")
async def start_link_workflow_json(
    _request: LinkWorkflowStartRequest,
) -> WorkflowResponse:
    return account_select.create_response()


@router.post("/link/workflow/next")
async def workflow_next(request: WorkflowNextRequest) -> WorkflowResponse:
    match request.pane_outputs[0]["pane_rendering_id"]:
        case "account_select":
            # Accounts confirmed, go to success
            return account_select_success.create_response()
        case "account_select_success":
            # Go to end
            return done.create_response()
        case unknown:
            raise ValueError(f"Unknown pane rendering id: {unknown}")
