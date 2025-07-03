import asyncio
import logging
import time

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
    cleanup_completed_flow,
    create_workflow_session_from_link_token,
    get_workflow_session,
    send_item_add_result_webhook,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/link/workflow/start")
async def start_link_workflow_json(
    request: LinkWorkflowStartRequest,
) -> WorkflowResponse:
    logger.info(f"Starting Link workflow: {request}")
    response, item_id = account_select.create_response()

    # Associate webhook with this workflow session if link token provided
    if t := request.link_token_configuration.link_token:
        session = create_workflow_session_from_link_token(t, response.workflow_session_id)
        session.item_id = item_id

    return response


@router.post("/link/workflow/next")
async def workflow_next(request: WorkflowNextRequest) -> WorkflowResponse:
    logger.info(f"Link workflow next: {request}")
    match request.pane_outputs[0]["pane_rendering_id"]:
        case "account_select":
            # User has selected accounts - track the selection
            workflow_session = get_workflow_session(request.workflow_session_id)
            if not workflow_session:
                raise ValueError(f"No workflow session found for {request.workflow_session_id}")

            if not workflow_session.item_id:
                raise ValueError(
                    f"No item ID found for workflow session: {request.workflow_session_id}"
                )

            workflow_session.selected_account_ids = request.pane_outputs[0]["user_selection"][
                "submit"
            ]["responses"][0]["response_ids"]

            # Accounts confirmed, go to success
            return account_select_success.create_response(request)
        case "account_select_success":
            # Go to end - this is where Link flow completes
            response = done.create_response(request)

            # Trigger ITEM_ADD_RESULT webhook (if configured)
            async def delayed_webhook() -> None:
                logger.info("Sleeping for 2 seconds")
                time.sleep(2)
                logger.info("Sending ITEM_ADD_RESULT webhook")
                await send_item_add_result_webhook(request.workflow_session_id)

                cleanup_completed_flow(request.workflow_session_id)

            asyncio.create_task(delayed_webhook())

            return response
        case unknown:
            raise ValueError(f"Unknown pane rendering id: {unknown}")
