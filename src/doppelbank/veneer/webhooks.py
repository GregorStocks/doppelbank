"""Webhook management for Link flows."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field

import httpx

from doppelbank.lib.ids import ItemId

logger = logging.getLogger(__name__)


@dataclass
class WorkflowSession:
    """Information associated with a workflow session."""

    session_id: str
    item_id: ItemId | None = None
    webhook_url: str | None = None
    selected_account_ids: list[str] = field(default_factory=list)
    public_token: str | None = None


# In-memory storage for workflow tracking
# TODO: Persist
_link_token_to_workflow_session: dict[str, str] = {}
_public_token_to_workflow_session: dict[str, str] = {}
_workflow_sessions: dict[str, WorkflowSession] = {}


def initialize_workflow_session(link_token: str, webhook_url: str | None = None) -> None:
    """Store link token data including optional webhook URL."""
    workflow_session_id = f"session:{uuid.uuid4()}"
    public_token = f"public-token:{uuid.uuid4()}"

    _link_token_to_workflow_session[link_token] = workflow_session_id
    _workflow_sessions[workflow_session_id] = WorkflowSession(
        session_id=workflow_session_id, webhook_url=webhook_url, public_token=public_token
    )
    _public_token_to_workflow_session[public_token] = workflow_session_id
    logger.info(f"Stored {link_token=} {webhook_url=} {workflow_session_id=}")


def get_workflow_session_from_link_token(link_token: str) -> WorkflowSession:
    return _workflow_sessions[_link_token_to_workflow_session[link_token]]


def get_workflow_session_from_public_token(public_token: str) -> WorkflowSession:
    return _workflow_sessions[_public_token_to_workflow_session[public_token]]


def get_workflow_session(workflow_session_id: str) -> WorkflowSession | None:
    """Get workflow session object for a workflow session ID."""
    return _workflow_sessions.get(workflow_session_id)


async def send_webhook(webhook_url: str, payload: dict) -> bool:
    """Send webhook payload to the specified URL.

    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Sending webhook to {webhook_url}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url, json=payload, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Webhook sent successfully to {webhook_url}")
            return True
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {e}")
        return False


async def send_item_add_result_webhook(workflow_session_id: str) -> None:
    """Send ITEM_ADD_RESULT webhook for completed Link flow."""
    workflow_session = get_workflow_session(workflow_session_id)
    if not workflow_session:
        raise ValueError(f"No workflow session found for {workflow_session_id}")

    if not workflow_session.webhook_url:
        logger.warning(f"No webhook configured for workflow session: {workflow_session_id}")
        return

    if not workflow_session.item_id:
        raise ValueError(f"No item ID found for workflow session: {workflow_session_id}")

    payload = {
        "webhook_type": "TRANSACTIONS",
        "webhook_code": "SYNC_UPDATES_AVAILABLE",
        "item_id": workflow_session.item_id.to_wire(),
        "initial_update_complete": True,
        "historical_update_complete": True,
        "environment": "sandbox",
    }

    # Send webhook asynchronously (don't block the response)
    asyncio.create_task(send_webhook(workflow_session.webhook_url, payload))
    logger.info(f"Queued ITEM_ADD_RESULT webhook for session: {workflow_session_id}")

    # TODO: Ideally don't leak memory (clean up the workflow session after a few minutes)
    # In practice it's not a big deal because we'll have like three users total before restarting the process.
