import logging

from fastapi import APIRouter

from doppelbank.veneer.endpoints.link.internal.models import (
    LinkWorkflowStartRequest,
    WorkflowNextRequest,
    WorkflowResponse,
)
from doppelbank.veneer.endpoints.link.internal.states import account_select

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/link/workflow/start")
async def start_link_workflow_json(
    request: LinkWorkflowStartRequest,
) -> WorkflowResponse:
    logger.info(f"Received link workflow start request: {request}")
    return account_select.create_account_select_response()


@router.post("/link/workflow/next")
async def workflow_next(request: WorkflowNextRequest) -> WorkflowResponse:
    logger.info(f"Workflow next request: {request}")
    pane_event = request.pane_event or {}
    event_type = pane_event.get("event_type")
    logger.info(f"Handling workflow next with event_type: {event_type}")
    return account_select.create_account_select_response()
