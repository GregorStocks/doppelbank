"""
Integration tests for the Veneer API with real HTTP requests.

This test file implements the "better tests" described in CLAUDE.md TODOs:
- Actually stand up a full server and query it via HTTP
- Single test that goes from Bedrock to Veneer
"""

import json
import multiprocessing
import shutil
import socket
import subprocess
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
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

    @pytest.fixture
    def running_server(self) -> Generator[None]:
        """Start a real Veneer server for integration testing."""
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
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
            pytest.fail("Server failed to start within timeout period")

        yield

        # Cleanup
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()

    def test_full_pipeline_with_http_requests(self, running_server: Any) -> None:
        """
        Test the complete pipeline: Bedrock -> Detritus -> Veneer with real HTTP requests.

        This implements the TODO: "Single test that goes from Bedrock to Veneer"
        """
        _ = running_server
        # Step 1: Generate complete persona data in one step using new hierarchical structure
        # Generate directly into the data directory structure
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "doppelbank.persona_generator.cli",
                "--user-id",
                "user_test",
                "--persona",
                "integration_test",
                "--institution",
                "doppelbank",
                "--account-type",
                "checking",
                "--seed",
                "12345",
                "--days",
                "60",  # Generate 60 days of data
            ],
            check=True,
        )

        # Verify hierarchical data was created
        hierarchical_account_file = (
            Path.cwd()
            / "data"
            / "personas"
            / "integration_test"
            / "doppelbank"
            / "checking.json"
        )
        assert (
            hierarchical_account_file.exists()
        ), f"Expected hierarchical data at {hierarchical_account_file}"

        with open(hierarchical_account_file) as f:
            detritus_data = json.load(f)
        assert "events" in detritus_data
        assert len(detritus_data["events"]) > 0

        # Step 2: Set up legacy flat data for backward compatibility testing
        veneer_data_dir = (
            Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        )
        veneer_data_dir.mkdir(exist_ok=True)

        # Copy the default test data for backward compatibility (flat structure)
        detritus_test_data_dir = Path(__file__).parent / "data" / "detritus"
        source_default_ledger = detritus_test_data_dir / "test_account.json"
        default_ledger_path = veneer_data_dir / "test_account.json"
        shutil.copy2(source_default_ledger, default_ledger_path)

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
            # Cleanup: remove the test files
            if default_ledger_path.exists():
                default_ledger_path.unlink()
            # Note: We don't clean up hierarchical_account_file as it's part of the data directory
            # and may be used by other tests or processes
