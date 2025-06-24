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


class TestVeneerAPI:
    """Test the Veneer API using FastAPI TestClient."""

    def test_transactions_sync_basic(self):
        """Test basic transactions sync endpoint using FastAPI TestClient."""
        client = TestClient(app)
        response = client.post("/transactions/sync", json={})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0

    def test_transactions_sync_with_format_param(self):
        """Test transactions sync with format parameter."""
        client = TestClient(app)
        response = client.post("/transactions/sync", json={"format": "json"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data

    def test_transactions_sync_with_account_id(self):
        """Test transactions sync with specific account_id parameter."""
        client = TestClient(app)
        response = client.post(
            "/transactions/sync", json={"options": {"account_id": "test_account"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "events" in data

    def test_transactions_sync_account_not_found(self):
        """Test error handling for non-existent account."""
        client = TestClient(app)
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": "nonexistent_account"}},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_transactions_sync_invalid_format(self):
        """Test error handling for invalid format parameter."""
        client = TestClient(app)
        response = client.post("/transactions/sync", json={"format": "invalid"})

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "unsupported" in data["detail"].lower()

    def test_validate_account_id_empty(self):
        """Test validation rejects empty account_id."""
        client = TestClient(app)
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": ""}},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "cannot be empty" in data["detail"]

    def test_validate_account_id_valid_characters(self):
        """Test validation accepts valid account_id characters."""
        client = TestClient(app)
        valid_accounts = [
            "test123",
            "my_account",
            "user-name",
            "account_123",
            "ABC123def",
            "a",
            "123",
            "test_account_123"
        ]
        
        for account_id in valid_accounts:
            response = client.post(
                "/transactions/sync",
                json={"options": {"account_id": account_id}},
            )
            # Should either succeed (200) or fail with 404 (file not found), but not 400 (validation error)
            assert response.status_code in [200, 404], f"Account ID '{account_id}' failed validation"

    def test_validate_account_id_invalid_characters(self):
        """Test validation rejects invalid characters."""
        client = TestClient(app)
        invalid_accounts = [
            "test@account",
            "user.name",
            "account#123",
            "test$account",
            "user%name",
            "account&123",
            "test*account",
            "user+name",
            "account=123",
            "test[account]",
            "user{name}",
            "account|123",
            "test\\account",
            "user/name",
            "account:123",
            "test;account",
            "user,name",
            "account<123>",
            "test?account",
            "user!name"
        ]
        
        for account_id in invalid_accounts:
            response = client.post(
                "/transactions/sync",
                json={"options": {"account_id": account_id}},
            )
            assert response.status_code == 400, f"Account ID '{account_id}' should have failed validation"
            data = response.json()
            assert "detail" in data
            assert "letters, numbers, underscores, and hyphens" in data["detail"]

    def test_validate_account_id_directory_traversal(self):
        """Test validation rejects directory traversal attempts."""
        client = TestClient(app)
        traversal_attempts = [
            "../test",
            "..\\test",
            "test/../other",
            "test\\..\\other",
            "..",
            "...",
            "test..",
            "..test",
            "test/",
            "test\\",
            "/test",
            "\\test"
        ]
        
        for account_id in traversal_attempts:
            response = client.post(
                "/transactions/sync",
                json={"options": {"account_id": account_id}},
            )
            assert response.status_code == 400, f"Account ID '{account_id}' should have failed validation"
            data = response.json()
            assert "detail" in data
            assert "letters, numbers, underscores, and hyphens" in data["detail"]

    def test_validate_account_id_length_limit(self):
        """Test validation enforces length limits."""
        client = TestClient(app)
        
        # Test maximum valid length (64 characters)
        max_valid = "a" * 64
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": max_valid}},
        )
        assert response.status_code in [200, 404], "64-character account ID should be valid"
        
        # Test exceeding maximum length (65 characters)
        too_long = "a" * 65
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": too_long}},
        )
        assert response.status_code == 400, "65-character account ID should fail validation"
        data = response.json()
        assert "detail" in data
        assert "1-64 characters" in data["detail"]

    def test_validate_account_id_edge_cases(self):
        """Test validation with edge cases."""
        client = TestClient(app)
        
        # Test with spaces
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": "test account"}},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "letters, numbers, underscores, and hyphens" in data["detail"]
        
        # Test with unicode characters
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": "tëst_åccount"}},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "letters, numbers, underscores, and hyphens" in data["detail"]
        
        # Test with null bytes
        response = client.post(
            "/transactions/sync",
            json={"options": {"account_id": "test\x00account"}},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "letters, numbers, underscores, and hyphens" in data["detail"]
