"""
FastAPI TestClient tests for the Veneer API.

These tests use FastAPI's TestClient for fast unit-style testing
without needing a real HTTP server.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doppelbank.veneer.cli import app

# Add this fixture at the top-level of the file
data_dir = Path(__file__).parent.parent / "src" / "doppelbank" / "veneer" / "data"


@pytest.fixture(scope="module", autouse=True)
def setup_test_ledger():
    """Create a minimal test_ledger_detritus.json in the veneer data directory for TestClient."""
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
                    "category": "Test Category",
                },
                "event_id": "1",
                "timestamp": "2024-01-01T00:00:00.000000Z",
            }
        ]
    }
    with open(test_ledger_path, "w") as f:
        json.dump(ledger, f)
    yield
    # Cleanup
    if test_ledger_path.exists():
        test_ledger_path.unlink()


class TestVeneerAPI:
    """Test the Veneer API using FastAPI TestClient."""

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
