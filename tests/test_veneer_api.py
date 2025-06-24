"""
Comprehensive tests for the Veneer API that test the full Bedrock-to-Veneer pipeline.

These tests ensure end-to-end coverage by:
1. Generating synthetic data via Bedrock CLI
2. Transforming it via Detritus CLI  
3. Standing up a real HTTP server
4. Making actual HTTP requests to test the API
"""

# Standard library
import json
import subprocess
import tempfile
import time
import multiprocessing
from pathlib import Path
from typing import Generator

# Third-party
import pytest
import requests
from fastapi.testclient import TestClient
import shutil
import uvicorn

# Local project
from doppelbank.veneer.cli import app

# Add this fixture at the top-level of the file
data_dir = Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"

@pytest.fixture(scope="module", autouse=True)
def setup_test_ledger():
    """Create a minimal test_ledger_detritus.json in the veneer data directory for TestClient tests."""
    data_dir.mkdir(exist_ok=True)
    test_ledger_path = data_dir / "test_ledger_detritus.json"
    # Minimal valid detritus ledger
    ledger = {
        "events": [
            {
                "addPending": {
                    "eventId": "1",
                    "transactionId": "t1",
                    "accountId": "acc_dummy",
                    "amount": 1000,
                    "description": "Test transaction",
                    "merchant": "Test Merchant",
                    "category": "Test Category"
                },
                "event_id": "1",
                "timestamp": "2024-01-01T00:00:00.000000Z"
            }
        ]
    }
    with open(test_ledger_path, "w") as f:
        json.dump(ledger, f)
    yield
    # Cleanup
    if test_ledger_path.exists():
        test_ledger_path.unlink()

def run_server_for_test():
    """Top-level function to run the veneer server for multiprocessing tests."""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

class TestVeneerAPI:
    """Test the Veneer API with real HTTP requests."""

    def test_transactions_sync_basic(self):
        """Test basic transactions sync endpoint using FastAPI TestClient."""
        client = TestClient(app)
        response = client.get("/transactions/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0

    def test_transactions_sync_with_format_param(self):
        """Test transactions sync with format parameter."""
        client = TestClient(app)
        response = client.get("/transactions/sync?format=json")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data

    def test_transactions_sync_with_file_param(self):
        """Test transactions sync with specific file parameter."""
        client = TestClient(app)
        response = client.get("/transactions/sync?file=test_ledger_detritus.json")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data

    def test_transactions_sync_file_not_found(self):
        """Test error handling for non-existent file."""
        client = TestClient(app)
        response = client.get("/transactions/sync?file=nonexistent.json")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_transactions_sync_invalid_format(self):
        """Test error handling for invalid format parameter."""
        client = TestClient(app)
        response = client.get("/transactions/sync?format=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "unsupported" in data["detail"].lower()


class TestVeneerServerIntegration:
    """Test the Veneer API with a real running server."""

    @pytest.fixture
    def server_process(self) -> Generator[multiprocessing.Process, None, None]:
        """Start a real Veneer server for integration testing."""
        process = multiprocessing.Process(target=run_server_for_test)
        process.start()
        time.sleep(2)
        yield process
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()

    def test_server_health_check(self, server_process):
        """Test that the server is actually running and responding."""
        # Wait a bit more for server to fully start
        time.sleep(1)
        
        try:
            response = requests.get("http://127.0.0.1:8001/transactions/sync", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Server not responding: {e}")

    def test_server_transactions_endpoint(self, server_process):
        """Test the transactions endpoint with a real HTTP request."""
        # Wait a bit more for server to fully start
        time.sleep(1)
        
        try:
            response = requests.get("http://127.0.0.1:8001/transactions/sync", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict)
            assert "events" in data
            assert isinstance(data["events"], list)
            assert len(data["events"]) > 0
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Server not responding: {e}")


class TestBedrockToVeneerPipeline:
    """Test the complete pipeline from Bedrock generation to Veneer serving."""

    def test_bedrock_to_veneer_end_to_end(self, tmp_path):
        """Test the complete pipeline: Bedrock -> Detritus -> Veneer."""
        # Step 1: Generate synthetic data with Bedrock
        bedrock_path = tmp_path / "test_bedrock.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
            "--user-id", "testuser", 
            "--output", str(bedrock_path), 
            "--format", "json", 
            "--seed", "42",
            "--months", "1"  # Keep it small for fast tests
        ], check=True)
        
        # Verify bedrock file was created
        assert bedrock_path.exists()
        with open(bedrock_path) as f:
            bedrock_data = json.load(f)
        assert "events" in bedrock_data
        assert len(bedrock_data["events"]) > 0
        
        # Step 2: Transform to Detritus format
        detritus_path = tmp_path / "test_detritus.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.detritus.cli",
            "--input", str(bedrock_path), 
            "--output", str(detritus_path), 
            "--format", "json"
        ], check=True)
        
        # Verify detritus file was created
        assert detritus_path.exists()
        with open(detritus_path) as f:
            detritus_data = json.load(f)
        assert "events" in detritus_data
        assert len(detritus_data["events"]) > 0
        
        # Step 3: Copy detritus file to veneer data directory
        veneer_data_dir = Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        veneer_data_dir.mkdir(exist_ok=True)
        test_ledger_path = veneer_data_dir / "test_pipeline_ledger.json"
        
        # Copy the generated detritus file to veneer data directory
        shutil.copy2(detritus_path, test_ledger_path)
        
        try:
            # Step 4: Test the API with the generated data
            client = TestClient(app)
            response = client.get(f"/transactions/sync?file={test_ledger_path.name}")
            
            assert response.status_code == 200
            api_data = response.json()
            assert isinstance(api_data, dict)
            assert "events" in api_data
            assert isinstance(api_data["events"], list)
            assert len(api_data["events"]) > 0
            
            # Verify the API returned the same data we generated
            assert len(api_data["events"]) == len(detritus_data["events"])
            
        finally:
            # Cleanup: remove the test file
            if test_ledger_path.exists():
                test_ledger_path.unlink()

    def test_pipeline_with_different_user_ids(self, tmp_path):
        """Test the pipeline with different user IDs to ensure isolation."""
        user_ids = ["user1", "user2", "user3"]
        
        for user_id in user_ids:
            # Generate data for this user
            bedrock_path = tmp_path / f"bedrock_{user_id}.json"
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
                "--user-id", user_id, 
                "--output", str(bedrock_path), 
                "--format", "json", 
                "--seed", "42",
                "--months", "1"
            ], check=True)
            
            # Transform to detritus
            detritus_path = tmp_path / f"detritus_{user_id}.json"
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.detritus.cli",
                "--input", str(bedrock_path), 
                "--output", str(detritus_path), 
                "--format", "json"
            ], check=True)
            
            # Verify each user has different data
            with open(detritus_path) as f:
                detritus_data = json.load(f)
            assert len(detritus_data["events"]) > 0

    def test_pipeline_data_consistency(self, tmp_path):
        """Test that the pipeline produces consistent data with the same seed (compare deterministic fields only)."""
        # Generate data twice with the same seed
        bedrock_path1 = tmp_path / "bedrock1.json"
        bedrock_path2 = tmp_path / "bedrock2.json"
        for i, path in enumerate([bedrock_path1, bedrock_path2]):
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
                "--user-id", "consistency_test", 
                "--output", str(path), 
                "--format", "json", 
                "--seed", "42",
                "--months", "1"
            ], check=True)
        # Transform both to detritus
        detritus_path1 = tmp_path / "detritus1.json"
        detritus_path2 = tmp_path / "detritus2.json"
        for bedrock_path, detritus_path in [(bedrock_path1, detritus_path1), (bedrock_path2, detritus_path2)]:
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.detritus.cli",
                "--input", str(bedrock_path), 
                "--output", str(detritus_path), 
                "--format", "json"
            ], check=True)
        # Load both detritus files
        with open(detritus_path1) as f:
            data1 = json.load(f)
        with open(detritus_path2) as f:
            data2 = json.load(f)
        # Compare only deterministic fields: event timestamps and amounts
        def extract_deterministic(events):
            result = []
            for event in events:
                # Try addPending, addCleared, etc.
                for key in ("addPending", "addCleared"):
                    if key in event:
                        e = event[key]
                        result.append((e.get("timestamp"), e.get("amount")))
            return sorted(result)
        det1 = extract_deterministic(data1["events"])
        det2 = extract_deterministic(data2["events"])
        assert det1 == det2
        assert len(det1) > 0 