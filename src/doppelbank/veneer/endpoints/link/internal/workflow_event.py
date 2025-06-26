import logging

from fastapi import APIRouter

from doppelbank.veneer.common import VeneerRequest, VeneerResponse

router = APIRouter()
logger = logging.getLogger(__name__)


class WorkflowEventRequest(VeneerRequest):
    pass


class WorkflowEventResponse(VeneerResponse):
    request_id: str


@router.post("/link/workflow/event")
async def workflow_event(_request: WorkflowEventRequest) -> WorkflowEventResponse:
    return WorkflowEventResponse(request_id="ok")
