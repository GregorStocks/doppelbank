import logging
import uuid

from doppelbank.veneer.common import VeneerResponse

logger = logging.getLogger(__name__)


class WorkflowResponse(VeneerResponse):
    workflow_session_id: str
    continuation_token: str
    next_pane: str
    heartbeat_configuration: dict[str, int]
    request_id: str


class WorkflowState:
    @staticmethod
    def get_credentials_pane() -> str:
        return "aaaa"

    @staticmethod
    def create_response(
        next_pane: str,
        workflow_session_id: str | None = None,
        continuation_token: str | None = None,
    ) -> WorkflowResponse:
        return WorkflowResponse(
            workflow_session_id=workflow_session_id or str(uuid.uuid4()),
            continuation_token=continuation_token or f"default:{uuid.uuid4()}",
            next_pane=next_pane,
            heartbeat_configuration={"interval_ms": 25000},
            request_id=str(uuid.uuid4()),
        )

    @staticmethod
    def handle_start() -> WorkflowResponse:
        logger.info("Starting workflow - going to credentials pane")
        return WorkflowState.create_response(WorkflowState.get_credentials_pane())

    @staticmethod
    def handle_next(
        event_type: str | None, _continuation_token: str | None = None
    ) -> WorkflowResponse:
        logger.info(f"Handling workflow next with event_type: {event_type}")

        # TODO: Handle events
        return WorkflowState.create_response(WorkflowState.get_credentials_pane())
