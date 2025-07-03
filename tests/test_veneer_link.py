"""
Tests for Veneer webhook functionality.

These tests verify that webhooks are properly triggered during the Link flow
and that the correct payloads are sent to configured webhook URLs.
"""

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from doppelbank.veneer.app import app
from doppelbank.veneer.webhooks import (
    associate_webhook_with_workflow,
    get_webhook_for_workflow,
    store_webhook_for_link_token,
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment() -> Generator[None]:
    """Configure VENEER_DATA_DIR to point to organized test data."""
    detritus_test_data_dir = Path(__file__).parent / "data" / "detritus"
    original_env = os.environ.get("VENEER_DATA_DIR")

    # Set environment variable to point to organized test data
    os.environ["VENEER_DATA_DIR"] = str(detritus_test_data_dir)

    yield

    # Restore original environment
    if original_env is not None:
        os.environ["VENEER_DATA_DIR"] = original_env
    else:
        os.environ.pop("VENEER_DATA_DIR", None)


class TestVeneerWebhooks:
    """Test webhook functionality in the Veneer API."""

    def test_webhook_flow_end_to_end(self) -> None:
        """Test complete webhook flow from link token create through completion."""
        client = TestClient(app)
        webhook_url = "https://example.com/webhook"
        received_webhooks = []

        async def mock_send_webhook(url: str, payload: dict) -> bool:
            """Mock webhook sender that captures payloads."""
            received_webhooks.append({"url": url, "payload": payload})
            return True

        with patch(
            "doppelbank.veneer.webhooks.send_webhook", side_effect=mock_send_webhook
        ):
            # Step 1: Create link token with webhook
            response = client.post(
                "/link/token/create",
                json={
                    "client_name": "Test App",
                    "country_codes": ["US"],
                    "language": "en",
                    "user": {"client_user_id": "test_user"},
                    "products": ["auth", "transactions"],
                    "webhook": webhook_url,
                },
            )
            assert response.status_code == 200
            link_data = response.json()
            link_token = link_data["link_token"]
            assert link_token.startswith("link-devenv-")

            # Step 2: Start workflow
            response = client.post(
                "/link/workflow/start",
                json={
                    "link_token_configuration": {
                        "link_token": link_token,
                        "institution_id": None,
                    }
                },
            )
            assert response.status_code == 200
            start_data = response.json()
            assert start_data["next_pane"]["id"] == "account_select"
            workflow_session_id = start_data["workflow_session_id"]
            assert workflow_session_id

            # Step 3: Progress to account_select_success
            response = client.post(
                "/link/workflow/next",
                json={
                    "workflow_session_id": workflow_session_id,
                    "pane_outputs": [{"pane_rendering_id": "account_select"}],
                },
            )
            assert response.status_code == 200
            assert response.json()["next_pane"]["id"] == "account_select_success"

            # Step 4: Complete flow (should trigger webhook)
            response = client.post(
                "/link/workflow/next",
                json={
                    "workflow_session_id": workflow_session_id,
                    "pane_outputs": [{"pane_rendering_id": "account_select_success"}],
                },
            )
            assert response.status_code == 200
            done_data = response.json()
            assert done_data["next_pane"]["id"] == "done"

            # Verify public token in response
            public_token = done_data["next_pane"]["sink"]["public_token"]
            assert public_token == "beep boop token token"

            # Verify webhook was sent
            assert len(received_webhooks) == 1
            webhook_call: dict = received_webhooks[0]

            assert webhook_call["url"] == webhook_url
            payload: dict = webhook_call["payload"]
            assert payload["webhook_type"] == "TRANSACTIONS"
            assert payload["webhook_code"] == "SYNC_UPDATES_AVAILABLE"
            assert payload["environment"] == "sandbox"
            assert payload["item_id"] == "default_item_id"

    def test_link_flow_without_webhook(self) -> None:
        """Test Link flow completes normally when no webhook is configured."""
        client = TestClient(app)
        received_webhooks = []

        async def mock_send_webhook(url: str, payload: dict) -> bool:
            """Mock webhook sender that captures payloads."""
            received_webhooks.append({"url": url, "payload": payload})
            return True

        with patch(
            "doppelbank.veneer.webhooks.send_webhook", side_effect=mock_send_webhook
        ):
            # Create link token WITHOUT webhook
            response = client.post(
                "/link/token/create",
                json={
                    "client_name": "Test App",
                    "country_codes": ["US"],
                    "language": "en",
                    "user": {"client_user_id": "test_user"},
                    "products": ["auth", "transactions"],
                    # No webhook field
                },
            )
            assert response.status_code == 200
            link_data = response.json()
            link_token = link_data["link_token"]

            # Start workflow
            response = client.post(
                "/link/workflow/start",
                json={
                    "link_token_configuration": {
                        "link_token": link_token,
                        "institution_id": None,
                    }
                },
            )
            assert response.status_code == 200
            start_data = response.json()
            workflow_session_id = start_data["workflow_session_id"]

            # Progress through flow
            response = client.post(
                "/link/workflow/next",
                json={
                    "workflow_session_id": workflow_session_id,
                    "pane_outputs": [{"pane_rendering_id": "account_select"}],
                },
            )
            assert response.status_code == 200

            # Complete flow
            response = client.post(
                "/link/workflow/next",
                json={
                    "workflow_session_id": workflow_session_id,
                    "pane_outputs": [{"pane_rendering_id": "account_select_success"}],
                },
            )
            assert response.status_code == 200
            done_data = response.json()

            # Verify flow completed normally
            public_token = done_data["next_pane"]["sink"]["public_token"]
            assert public_token == "beep boop token token"

            # Verify NO webhook was sent
            assert len(received_webhooks) == 0

    def test_webhook_storage_and_association(self) -> None:
        """Test webhook storage and association with workflow sessions."""
        # Test storing webhook for link token
        link_token = "link-test-123"
        webhook_url = "https://myapp.com/webhook"
        store_webhook_for_link_token(link_token, webhook_url)

        # Test associating with workflow session
        workflow_session_id = "session-test-456"
        associate_webhook_with_workflow(link_token, workflow_session_id)

        # Test retrieving webhook for workflow
        retrieved_url = get_webhook_for_workflow(workflow_session_id)
        assert retrieved_url == webhook_url

        # Test non-existent workflow
        non_existent_url = get_webhook_for_workflow("non-existent-session")
        assert non_existent_url is None
