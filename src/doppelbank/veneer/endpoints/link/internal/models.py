from typing import Any

from doppelbank.veneer.common import VeneerRequest, VeneerResponse


class LinkTokenConfiguration(VeneerRequest):
    link_token: str
    institution_id: str | None = None


class LinkWorkflowStartRequest(VeneerRequest):
    link_token_configuration: LinkTokenConfiguration


class WorkflowNextRequest(VeneerRequest):
    pane_outputs: list[dict[str, Any]]
    workflow_session_id: str | None = None  # Track which workflow session this is


class WorkflowResponse(VeneerResponse):
    workflow_session_id: str
    continuation_token: str
    next_pane: dict[str, Any]
    additional_panes: list[Any]
    request_id: str
    queued_sdk_events: list[Any]
