from typing import Any

from doppelbank.veneer.common import VeneerRequest, VeneerResponse


class WorkflowResponse(VeneerResponse):
    workflow_session_id: str
    continuation_token: str
    next_pane: dict[str, Any]
    additional_panes: list[Any]
    request_id: str
    queued_sdk_events: list[Any]


class LinkWorkflowStartRequest(VeneerRequest):
    pass


class WorkflowNextRequest(VeneerRequest):
    continuation_token: str | None = None
    pane_event: dict[str, Any] | None = None
    user_input: dict[str, Any] | None = None
