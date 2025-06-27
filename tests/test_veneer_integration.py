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

    def test_full_pipeline_with_http_requests(
        self, running_server: Any, tmp_path: Path
    ) -> None:
        """
        Test the complete pipeline: Bedrock -> Detritus -> Veneer with real HTTP requests.

        This implements the TODO: "Single test that goes from Bedrock to Veneer"
        """
        _ = running_server
        # Step 1: Generate complete persona data in one step
        detritus_path = tmp_path / "integration_detritus.json"
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "doppelbank.persona_generator.cli",
                "--user-id",
                "integration_test_user",
                "--persona",
                "integration_test",
                "--institution",
                "doppelbank",
                "--account-type",
                "checking",
                "--output",
                str(detritus_path),
                "--format",
                "json",
                "--seed",
                "12345",
                "--days",
                "60",  # Generate 60 days of data
            ],
            check=True,
        )

        # Verify detritus file was created and has data
        assert detritus_path.exists()
        with open(detritus_path) as f:
            detritus_data = json.load(f)
        assert "events" in detritus_data
        assert len(detritus_data["events"]) > 0

        # Step 2: Set up both flat and hierarchical data for backward compatibility testing
        veneer_data_dir = (
            Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        )
        veneer_data_dir.mkdir(exist_ok=True)

        # Copy the default test data for backward compatibility (flat structure)
        detritus_test_data_dir = Path(__file__).parent / "data" / "detritus"
        source_default_ledger = detritus_test_data_dir / "test_account.json"
        default_ledger_path = veneer_data_dir / "test_account.json"
        shutil.copy2(source_default_ledger, default_ledger_path)

        # For hierarchical data, we'll rely on the generated data structure in ./data/
        # The persona generator already created the hierarchical structure
        # We just need to make sure the integration test data exists there
        hierarchical_account_id = (
            "integration_test_user-integration_test-doppelbank-checking"
        )
        hierarchical_account_file = (
            Path.cwd()
            / "data"
            / "personas"
            / "integration_test"
            / "doppelbank"
            / "checking.json"
        )

        # If the hierarchical file doesn't exist, copy our generated file there
        if not hierarchical_account_file.exists():
            hierarchical_account_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(detritus_path, hierarchical_account_file)

        try:
            # Step 3: Test the API with real HTTP requests (like curl)
            base_url = "http://127.0.0.1:8002"
            hierarchical_account_id = (
                "integration_test_user-integration_test-doppelbank-checking"
            )

            # Test 1: Basic health check with old flat account
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={
                    "access_token": "test_account",
                    "options": {"account_id": "test_account"},
                },
                timeout=10,
            )
            assert response.status_code == 200

            # Test 2: Query with hierarchical account_id
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={
                    "access_token": hierarchical_account_id,
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

            # Test 3: Test with format parameter
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={
                    "access_token": "test_account",
                    "options": {"account_id": "test_account"},
                    "format": "json",
                },
                timeout=10,
            )
            assert response.status_code == 200

            # Test 4: Test error handling for non-existent account
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={
                    "access_token": "nonexistent_account",
                    "options": {"account_id": "nonexistent_account"},
                },
                timeout=10,
            )
            assert response.status_code == 404

        finally:
            # Cleanup: remove the test files
            if default_ledger_path.exists():
                default_ledger_path.unlink()
            if hierarchical_account_file.exists():
                hierarchical_account_file.unlink()
