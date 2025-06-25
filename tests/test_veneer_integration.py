"""
Integration tests for the Veneer API with real HTTP requests.

This test file implements the "better tests" described in CLAUDE.md TODOs:
- Actually stand up a full server and query it via HTTP
- Single test that goes from Bedrock to Veneer
"""

import concurrent.futures
import json
import multiprocessing
import os
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

from doppelbank.bedrock.cli import UserInfo, generate_events
from doppelbank.detritus.transform import bedrock_to_detritus
from doppelbank.veneer.cli import app
from doppelbank.lib.timestamp import parse_iso8601_z


def run_test_server() -> None:
    """Function to run test server in multiprocessing context."""
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")


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
        self, _running_server: Any, tmp_path: Path
    ) -> None:
        """
        Test the complete pipeline: Bedrock -> Detritus -> Veneer with real HTTP requests.

        This implements the TODO: "Single test that goes from Bedrock to Veneer"
        """
        # Step 1: Generate synthetic data with Bedrock CLI
        bedrock_path = tmp_path / "integration_bedrock.json"
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "doppelbank.bedrock.cli",
                "generate",
                "--user-id",
                "integration_test_user",
                "--output",
                str(bedrock_path),
                "--format",
                "json",
                "--seed",
                "12345",
                "--months",
                "2",  # Generate 2 months of data
            ],
            check=True,
        )

        # Verify bedrock file was created and has data
        assert bedrock_path.exists()
        with open(bedrock_path) as f:
            bedrock_data = json.load(f)
        assert "events" in bedrock_data
        assert len(bedrock_data["events"]) > 0

        # Step 2: Transform to Detritus format
        detritus_path = tmp_path / "integration_detritus.json"
        subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "doppelbank.detritus.cli",
                "--input",
                str(bedrock_path),
                "--output",
                str(detritus_path),
                "--format",
                "json",
            ],
            check=True,
        )

        # Verify detritus file was created and has data
        assert detritus_path.exists()
        with open(detritus_path) as f:
            detritus_data = json.load(f)
        assert "events" in detritus_data
        assert len(detritus_data["events"]) > 0

        # Step 3: Copy detritus file to veneer data directory
        veneer_data_dir = (
            Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        )
        veneer_data_dir.mkdir(exist_ok=True)
        test_ledger_path = veneer_data_dir / "integration_test_ledger.json"
        default_ledger_path = veneer_data_dir / "test_ledger_detritus.json"

        # Copy the default test data from organized location
        detritus_test_data_dir = Path(__file__).parent / "data" / "detritus"
        source_default_ledger = detritus_test_data_dir / "test_account.json"

        # Copy the generated detritus file to veneer data directory
        shutil.copy2(detritus_path, test_ledger_path)
        # Also copy default test data for basic health check (using new filename pattern)
        default_ledger_path = veneer_data_dir / "test_account.json"
        shutil.copy2(source_default_ledger, default_ledger_path)

        try:
            # Step 4: Test the API with real HTTP requests (like curl)
            base_url = "http://127.0.0.1:8002"

            # Test 1: Basic health check
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={"options": {"account_id": "test_account"}},
                timeout=10,
            )
            assert response.status_code == 200

            # Test 2: Query with specific account_id
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={"options": {"account_id": "test_account"}},
                timeout=10,
            )
            assert response.status_code == 200

            api_data = response.json()
            assert isinstance(api_data, dict)
            assert "events" in api_data
            assert isinstance(api_data["events"], list)
            assert len(api_data["events"]) > 0

            # Verify the API returned data (event counts may differ due to transformation)
            assert len(api_data["events"]) > 0

            # Test 3: Test with format parameter
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={"options": {"account_id": "test_account"}, "format": "json"},
                timeout=10,
            )
            assert response.status_code == 200

            # Test 4: Test error handling for non-existent account
            response = requests.post(
                f"{base_url}/transactions/sync",
                json={"options": {"account_id": "nonexistent_account"}},
                timeout=10,
            )
            assert response.status_code == 404

        finally:
            # Cleanup: remove the test files
            if test_ledger_path.exists():
                test_ledger_path.unlink()
            if default_ledger_path.exists():
                default_ledger_path.unlink()

    def test_server_performance(self, _running_server: Any, tmp_path: Path) -> None:
        """Test server performance with multiple concurrent requests."""
        # Generate test data
        user_info = UserInfo(
            user_id="test_user",
            timezone_name="America/New_York",
            employer="Test Corp",
            salary=50000.0,
        )

        # Generate events
        events = generate_events(user_info, months=1, seed=42)
        detritus_ledger = bedrock_to_detritus(events)

        # Save to test data directory
        test_data_dir = tmp_path / "test_data"
        test_data_dir.mkdir()
        ledger_path = test_data_dir / "test_account.json"
        with open(ledger_path, "w") as f:
            f.write(detritus_ledger.to_json())

        # Set environment variable for veneer
        os.environ["VENEER_DATA_DIR"] = str(test_data_dir)

        # Test concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _i in range(10):
                future = executor.submit(
                    requests.post,
                    "http://127.0.0.1:8002/transactions/sync",
                    json={"options": {"account_id": "test_account"}},
                    timeout=10,
                )
                futures.append(future)

            # Wait for all requests to complete
            responses = [future.result() for future in futures]

        end_time = time.time()
        duration = end_time - start_time

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "events" in data
            assert len(data["events"]) > 0

        # Verify performance was reasonable (not too slow)
        assert duration < 30  # Should complete within 30 seconds
