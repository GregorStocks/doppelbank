"""Webhook management for Link flows."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

# In-memory storage for webhook tracking
# TODO: Persist
_link_token_to_webhook: dict[str, str] = {}
_workflow_session_to_webhook: dict[str, str] = {}


def store_webhook_for_link_token(link_token: str, webhook_url: str) -> None:
    """Store webhook URL associated with a link token."""
    _link_token_to_webhook[link_token] = webhook_url
    logger.info(f"Stored webhook for link token: {link_token}")


def associate_webhook_with_workflow(link_token: str, workflow_session_id: str) -> None:
    """Associate stored webhook URL with a workflow session ID."""
    webhook_url = _link_token_to_webhook.get(link_token)
    if webhook_url:
        _workflow_session_to_webhook[workflow_session_id] = webhook_url
        logger.info(
            f"Associated webhook for link token {link_token} with workflow session:"
            f"{workflow_session_id}"
        )
    else:
        logger.warning(f"No webhook found for link token {link_token}")


def get_webhook_for_workflow(workflow_session_id: str) -> str | None:
    """Get webhook URL for a workflow session ID."""
    return _workflow_session_to_webhook.get(workflow_session_id)


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


async def send_item_add_result_webhook(workflow_session_id: str, item_id: str) -> None:
    """Send ITEM_ADD_RESULT webhook for completed Link flow."""
    webhook_url = get_webhook_for_workflow(workflow_session_id)
    if not webhook_url:
        logger.warning(f"No webhook configured for workflow session: {workflow_session_id}")
        return

    payload = {
        "webhook_type": "TRANSACTIONS",
        "webhook_code": "SYNC_UPDATES_AVAILABLE",
        "item_id": item_id,
        "initial_update_complete": True,
        "historical_update_complete": True,
        "environment": "sandbox",
    }

    # Send webhook asynchronously (don't block the response)
    asyncio.create_task(send_webhook(webhook_url, payload))
    logger.info(f"Queued ITEM_ADD_RESULT webhook for session: {workflow_session_id}")


def cleanup_completed_flow(workflow_session_id: str) -> None:
    """Clean up webhook tracking for completed flow."""
    _workflow_session_to_webhook.pop(workflow_session_id, None)
    # Note: We keep link_token mapping in case of retries
    logger.debug(f"Cleaned up webhook tracking for session: {workflow_session_id}")
