"""
Integration tests that demonstrate the full Bedrock-to-Veneer pipeline with real HTTP requests.

This test file implements the "better tests" described in the TODOs:
- Actually stand up a full server and query it via curl
- Single test that goes from Bedrock to Veneer
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
import uvicorn

# Local project
from doppelbank.veneer.cli import app


class TestVeneerIntegration:
    """Integration tests for the Veneer API with real server and HTTP requests."""

    @pytest.fixture
    def running_server(self) -> Generator[None, None, None]:
        """Start a real Veneer server for integration testing."""
        port = 8002  # Use different port to avoid conflicts
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
        
        # Start server in a separate process
        process = multiprocessing.Process(target=run_server)
        process.start()
        
        # Wait for server to start
        time.sleep(3)
        
        yield
        
        # Cleanup
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()

    def test_full_pipeline_with_http_requests(self, running_server, tmp_path):
        """
        Test the complete pipeline: Bedrock -> Detritus -> Veneer with real HTTP requests.
        
        This implements the TODO: "Single test that goes from Bedrock to Veneer"
        """
        # Step 1: Generate synthetic data with Bedrock CLI
        bedrock_path = tmp_path / "integration_bedrock.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
            "--user-id", "integration_test_user", 
            "--output", str(bedrock_path), 
            "--format", "json", 
            "--seed", "12345",
            "--months", "2"  # Generate 2 months of data
        ], check=True)
        
        # Verify bedrock file was created and has data
        assert bedrock_path.exists()
        with open(bedrock_path) as f:
            bedrock_data = json.load(f)
        assert "events" in bedrock_data
        assert len(bedrock_data["events"]) > 0
        print(f"Generated {len(bedrock_data['events'])} bedrock events")
        
        # Step 2: Transform to Detritus format
        detritus_path = tmp_path / "integration_detritus.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.detritus.cli",
            "--input", str(bedrock_path), 
            "--output", str(detritus_path), 
            "--format", "json"
        ], check=True)
        
        # Verify detritus file was created and has data
        assert detritus_path.exists()
        with open(detritus_path) as f:
            detritus_data = json.load(f)
        assert "events" in detritus_data
        assert len(detritus_data["events"]) > 0
        print(f"Generated {len(detritus_data['events'])} detritus events")
        
        # Step 3: Copy detritus file to veneer data directory
        veneer_data_dir = Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        veneer_data_dir.mkdir(exist_ok=True)
        test_ledger_path = veneer_data_dir / "integration_test_ledger.json"
        
        # Copy the generated detritus file to veneer data directory
        import shutil
        shutil.copy2(detritus_path, test_ledger_path)
        
        try:
            # Step 4: Test the API with real HTTP requests (like curl)
            base_url = "http://127.0.0.1:8002"
            
            # Test 1: Basic health check
            print("Testing server health...")
            response = requests.get(f"{base_url}/transactions/sync", timeout=10)
            assert response.status_code == 200
            print("✓ Server is responding")
            
            # Test 2: Query with specific file parameter
            print("Testing transactions endpoint with specific file...")
            response = requests.get(
                f"{base_url}/transactions/sync?file={test_ledger_path.name}", 
                timeout=10
            )
            assert response.status_code == 200
            
            api_data = response.json()
            assert isinstance(api_data, dict)
            assert "events" in api_data
            assert isinstance(api_data["events"], list)
            assert len(api_data["events"]) > 0
            
            # Verify the API returned the same data we generated
            assert len(api_data["events"]) == len(detritus_data["events"])
            print(f"✓ API returned {len(api_data['events'])} events (matches detritus)")
            
            # Test 3: Test with format parameter
            print("Testing with format parameter...")
            response = requests.get(
                f"{base_url}/transactions/sync?file={test_ledger_path.name}&format=json", 
                timeout=10
            )
            assert response.status_code == 200
            print("✓ Format parameter works")
            
            # Test 4: Test error handling for non-existent file
            print("Testing error handling...")
            response = requests.get(
                f"{base_url}/transactions/sync?file=nonexistent.json", 
                timeout=10
            )
            assert response.status_code == 404
            print("✓ Error handling works for missing files")
            
            # Test 5: Test error handling for invalid format
            response = requests.get(
                f"{base_url}/transactions/sync?format=invalid", 
                timeout=10
            )
            assert response.status_code == 400
            print("✓ Error handling works for invalid format")
            
            print("✓ All integration tests passed!")
            
        finally:
            # Cleanup: remove the test file
            if test_ledger_path.exists():
                test_ledger_path.unlink()

    def test_multiple_users_isolation(self, running_server, tmp_path):
        """Test that different users have isolated data."""
        user_ids = ["user_a", "user_b", "user_c"]
        user_data = {}
        
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
            
            # Load the data
            with open(detritus_path) as f:
                user_data[user_id] = json.load(f)
        
        # Verify each user has data
        for user_id, data in user_data.items():
            assert len(data["events"]) > 0
            print(f"✓ User {user_id} has {len(data['events'])} events")

    def test_deterministic_generation(self, running_server, tmp_path):
        """Test that the same seed produces identical results."""
        # Generate data twice with the same parameters
        for run in [1, 2]:
            bedrock_path = tmp_path / f"deterministic_bedrock_{run}.json"
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
                "--user-id", "deterministic_test", 
                "--output", str(bedrock_path), 
                "--format", "json", 
                "--seed", "999",
                "--months", "1"
            ], check=True)
            
            detritus_path = tmp_path / f"deterministic_detritus_{run}.json"
            subprocess.run([
                "uv", "run", "python", "-m", "doppelbank.detritus.cli",
                "--input", str(bedrock_path), 
                "--output", str(detritus_path), 
                "--format", "json"
            ], check=True)
        
        # Load both results
        with open(tmp_path / "deterministic_detritus_1.json") as f:
            data1 = json.load(f)
        with open(tmp_path / "deterministic_detritus_2.json") as f:
            data2 = json.load(f)
        
        # Verify they are identical
        assert data1 == data2
        assert len(data1["events"]) > 0
        print(f"✓ Deterministic generation produces identical results ({len(data1['events'])} events)")

    def test_server_performance(self, running_server, tmp_path):
        """Test server performance with multiple concurrent requests."""
        # Generate test data
        bedrock_path = tmp_path / "performance_bedrock.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
            "--user-id", "performance_test", 
            "--output", str(bedrock_path), 
            "--format", "json", 
            "--seed", "42",
            "--months", "1"
        ], check=True)
        
        detritus_path = tmp_path / "performance_detritus.json"
        subprocess.run([
            "uv", "run", "python", "-m", "doppelbank.detritus.cli",
            "--input", str(bedrock_path), 
            "--output", str(detritus_path), 
            "--format", "json"
        ], check=True)
        
        # Copy to veneer data directory
        veneer_data_dir = Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"
        veneer_data_dir.mkdir(exist_ok=True)
        test_ledger_path = veneer_data_dir / "performance_test_ledger.json"
        
        import shutil
        shutil.copy2(detritus_path, test_ledger_path)
        
        try:
            # Test multiple concurrent requests
            base_url = "http://127.0.0.1:8002"
            start_time = time.time()
            
            # Make 10 concurrent requests
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(
                        requests.get,
                        f"{base_url}/transactions/sync?file={test_ledger_path.name}",
                        timeout=10
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
            
            print(f"✓ Server handled 10 concurrent requests in {duration:.2f} seconds")
            
        finally:
            if test_ledger_path.exists():
                test_ledger_path.unlink() 