import logging

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest

from .workflow_shared import WorkflowResponse, WorkflowState

router = APIRouter()
logger = logging.getLogger(__name__)


class LinkWorkflowStartRequest(VeneerRequest):
    pass


@router.post("/link/workflow/start")
async def start_link_workflow_json(
    request: LinkWorkflowStartRequest,
) -> WorkflowResponse:
    logger.info(f"Received link workflow start request: {request}")
    return WorkflowState.handle_start()
