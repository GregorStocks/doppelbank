from typing import Any

from doppelbank.veneer.common import VeneerRequest, VeneerResponse


class LinkWorkflowStartRequest(VeneerRequest):
    pass


class WorkflowNextRequest(VeneerRequest):
    pane_outputs: list[dict[str, Any]]


class WorkflowResponse(VeneerResponse):
    workflow_session_id: str
    continuation_token: str
    next_pane: dict[str, Any]
    additional_panes: list[Any]
    request_id: str
    queued_sdk_events: list[Any]
