import logging
from typing import Any

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest

from .workflow_shared import WorkflowResponse, WorkflowState

router = APIRouter()
logger = logging.getLogger(__name__)


class WorkflowNextRequest(VeneerRequest):
    continuation_token: str | None = None
    pane_event: dict[str, Any] | None = None
    user_input: dict[str, Any] | None = None


@router.post("/link/workflow/next")
async def workflow_next(request: WorkflowNextRequest) -> WorkflowResponse:
    logger.info(f"Workflow next request: {request}")
    continuation_token = request.continuation_token
    pane_event = request.pane_event or {}
    _ = request.user_input or {}
    event_type = pane_event.get("event_type")
    return WorkflowState.handle_next(event_type, continuation_token)
