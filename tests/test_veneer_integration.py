"""
Integration tests for the Veneer API with real HTTP requests.

This test file implements the "better tests" described in CLAUDE.md TODOs:
- Actually stand up a full server and query it via HTTP
- Single test that goes from Bedrock to Veneer
"""

import multiprocessing
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import requests
import uvicorn

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.app import app


def run_test_server() -> None:
    """Function to run test server in multiprocessing context."""
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="debug", access_log=True)


class TestVeneerIntegration:
    """Integration tests for the Veneer API with real server and HTTP requests."""

    def _check_server_ready(self, host: str, port: int) -> bool:
        """Check if server is ready using a quick socket connection."""
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True
        except OSError:
            return False

    def test_full_pipeline_with_http_requests(self) -> None:
        """
        Test the complete pipeline: Persona Generator -> Veneer with real HTTP requests.
        """

        # Create a temporary directory for test data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            subprocess.run(
                [
                    "uv",
                    "run",
                    "persona_generator",
                    "--persona",
                    "integration_test",
                    "--institution",
                    "doppelbank",
                    "--account-type",
                    "checking",
                    "--days",
                    "60",  # Generate 60 days of data
                    "--output-dir",
                    temp_path,
                ],
                check=True,
            )

            # Set environment variables to point to temporary directories
            original_data_dir = os.environ.get("VENEER_DATA_DIR", "")

            os.environ["VENEER_DATA_DIR"] = str(temp_path)

            # Start server in a separate process
            process = multiprocessing.Process(target=run_test_server)
            process.start()

            # Give server minimal time to start, then use rapid polling
            time.sleep(0.5)  # 500ms minimal start time

            # Then rapid polling with no additional sleeps
            max_attempts = 50  # Should be more than enough with 0.1s timeout each
            server_ready = False
            for _ in range(max_attempts):
                if self._check_server_ready("127.0.0.1", 8002):
                    server_ready = True
                    break
            if not server_ready:
                raise RuntimeError("Server failed to start")

            try:
                # Step 3: Test the API with real HTTP requests (like curl)
                base_url = "http://127.0.0.1:8002"

                # Create hierarchical IDs and access token for testing
                item_id = ItemId("user_test", "integration_test", "doppelbank")
                access_token = item_id.create_access_token()
                hierarchical_account_id = f"{item_id.to_wire()}-checking"

                # Test 1: Query with hierarchical account_id
                response = requests.post(
                    f"{base_url}/transactions/sync",
                    json={
                        "access_token": access_token,
                        "options": {"account_id": hierarchical_account_id},
                    },
                    timeout=10,
                )
                assert response.status_code == 200

                api_data = response.json()
                assert isinstance(api_data, dict)
                assert "accounts" in api_data
                assert "added" in api_data
                assert isinstance(api_data["accounts"], list)
                assert isinstance(api_data["added"], list)
                assert len(api_data["accounts"]) > 0

                # Verify the API returned data (event counts may differ due to transformation)
                assert len(api_data["added"]) > 0

                # Test error handling for non-existent account
                nonexistent_item_id = ItemId("user_test", "nonexistent", "nonexistent")
                nonexistent_access_token = nonexistent_item_id.create_access_token()
                nonexistent_account_id = f"{nonexistent_item_id.to_wire()}-nonexistent"

                response = requests.post(
                    f"{base_url}/transactions/sync",
                    json={
                        "access_token": nonexistent_access_token,
                        "options": {"account_id": nonexistent_account_id},
                    },
                    timeout=10,
                )
                assert response.status_code == 404

            finally:
                # Restore original environment variables
                os.environ["VENEER_DATA_DIR"] = original_data_dir

                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
