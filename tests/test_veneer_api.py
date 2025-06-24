"""
FastAPI TestClient tests for the Veneer API.

These tests use FastAPI's TestClient for fast unit-style testing
without needing a real HTTP server.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doppelbank.veneer.cli import app


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Configure VENEER_DATA_DIR to point to organized test data."""
    detritus_test_data_dir = Path(__file__).parent.parent / "data" / "detritus"
    original_env = os.environ.get("VENEER_DATA_DIR")

    # Set environment variable to point to organized test data
    os.environ["VENEER_DATA_DIR"] = str(detritus_test_data_dir)

    yield

    # Restore original environment
    if original_env is not None:
        os.environ["VENEER_DATA_DIR"] = original_env
    else:
        os.environ.pop("VENEER_DATA_DIR", None)


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
