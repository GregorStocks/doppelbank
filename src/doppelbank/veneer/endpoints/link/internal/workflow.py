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
from doppelbank.veneer.webhooks import (
    associate_webhook_with_workflow,
    cleanup_completed_flow,
    send_item_add_result_webhook,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/link/workflow/start")
async def start_link_workflow_json(
    request: LinkWorkflowStartRequest,
) -> WorkflowResponse:
    logger.info(f"Starting Link workflow: {request}")
    response = account_select.create_response()

    # Associate webhook with this workflow session if link token provided
    if t := request.link_token_configuration.link_token:
        associate_webhook_with_workflow(t, response.workflow_session_id)

    return response


@router.post("/link/workflow/next")
async def workflow_next(request: WorkflowNextRequest) -> WorkflowResponse:
    logger.info(f"Link workflow next: {request}")
    match request.pane_outputs[0]["pane_rendering_id"]:
        case "account_select":
            # Accounts confirmed, go to success
            return account_select_success.create_response()
        case "account_select_success":
            # Go to end - this is where Link flow completes
            response = done.create_response()

            # Trigger ITEM_ADD_RESULT webhook if configured
            if request.workflow_session_id:
                # Extract public token from done response
                public_token = response.next_pane.get("sink", {}).get("public_token")
                if public_token:
                    await send_item_add_result_webhook(
                        request.workflow_session_id, public_token
                    )
                    cleanup_completed_flow(request.workflow_session_id)

            return response
        case unknown:
            raise ValueError(f"Unknown pane rendering id: {unknown}")
