"""Webhook management for Link flows."""

import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from doppelbank.lib.ids import ItemId

logger = logging.getLogger(__name__)


@dataclass
class WorkflowSession:
    """Information associated with a workflow session."""

    webhook_url: str | None = None
    item_id: ItemId | None = None
    selected_account_ids: list[str] = field(default_factory=list)


# In-memory storage for workflow tracking
# TODO: Persist
_link_token_to_webhook: dict[str, str | None] = {}
_workflow_sessions: dict[str, WorkflowSession] = {}


def store_webhook_for_link_token(link_token: str, webhook_url: str | None = None) -> None:
    """Store link token data including optional webhook URL."""
    _link_token_to_webhook[link_token] = webhook_url
    logger.info(f"Stored link token {link_token} with webhook: {webhook_url}")


def create_workflow_session_from_link_token(
    link_token: str, workflow_session_id: str
) -> WorkflowSession:
    """Create workflow session from link token data."""
    webhook_url = _link_token_to_webhook.pop(link_token, None)

    session = WorkflowSession(webhook_url=webhook_url, item_id=None, selected_account_ids=[])
    _workflow_sessions[workflow_session_id] = session

    if webhook_url:
        logger.info(f"Created workflow session {workflow_session_id} with webhook: {webhook_url}")
    else:
        logger.info(f"Created workflow session {workflow_session_id} without webhook")

    return session


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


def cleanup_completed_flow(workflow_session_id: str) -> None:
    """Clean up workflow session tracking for completed flow."""
    _workflow_sessions.pop(workflow_session_id, None)
    logger.debug(f"Cleaned up workflow session tracking for session: {workflow_session_id}")
