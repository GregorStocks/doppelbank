"""
FastAPI TestClient tests for the Veneer API.

These tests use FastAPI's TestClient for fast unit-style testing
without needing a real HTTP server.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doppelbank.veneer.app import app


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


class TestVeneerAPI:
    """Test the Veneer API using FastAPI TestClient."""

    def test_transactions_sync_basic(self) -> None:
        """Test basic transactions sync endpoint using FastAPI TestClient."""
        client = TestClient(app)
        response = client.post(
            "/transactions/sync",
            json={
                "access_token": "test_account|123",
                "options": {"account_id": "test_account"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "accounts" in data
        assert "added" in data
        assert "modified" in data
        assert "removed" in data
        assert "next_cursor" in data
        assert "has_more" in data
        assert "request_id" in data
        assert isinstance(data["accounts"], list)
        assert isinstance(data["added"], list)
        assert len(data["accounts"]) > 0

    def test_transactions_sync_account_not_found(self) -> None:
        """Test error handling for non-existent account."""
        client = TestClient(app)
        response = client.post(
            "/transactions/sync",
            json={
                "access_token": "nonexistent_account|123",
                "options": {"account_id": "nonexistent_account"},
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_validate_account_id_valid_characters(self) -> None:
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
            "test_account_123",
        ]

        for account_id in valid_accounts:
            response = client.post(
                "/transactions/sync",
                json={
                    "access_token": f"{account_id}|123",
                    "options": {"account_id": account_id},
                },
            )
            # Should either succeed (200) or fail with 404 (file not found),
            # but not 400 (validation error)
            assert response.status_code in [
                200,
                404,
            ], f"Account ID '{account_id}' failed validation"

    def test_validate_account_id_invalid_characters(self) -> None:
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
            "test\\account",
            "user/name",
            "account:123",
            "test;account",
            "user,name",
            "account<123>",
            "test?account",
            "user!name",
            "tëst_åccount",
            "../test",
            "/test",
            "test\x00account",
            "",
        ]

        for account_id in invalid_accounts:
            response = client.post(
                "/transactions/sync",
                json={
                    "access_token": f"{account_id}|123",
                },
            )
            assert (
                response.status_code == 400
            ), f"Account ID '{account_id}' should have failed validation"
            data = response.json()
            assert "detail" in data
            assert (
                "letters, numbers, underscores, and hyphens" in data["detail"]
            ), f"Account ID '{account_id}' should have failed validation"

            response = client.post(
                "/transactions/sync",
                json={
                    "access_token": f"{account_id}|123",
                    "options": {"account_id": account_id},
                },
            )
            assert (
                response.status_code == 400
            ), f"Account ID '{account_id}' should have failed validation"
            data = response.json()
            assert "detail" in data
            assert "letters, numbers, underscores, and hyphens" in data["detail"]

    def test_institutions_get_by_id_with_logo(self) -> None:
        """Test institutions/get_by_id endpoint returns logo from file."""
        client = TestClient(app)
        response = client.post(
            "/institutions/get_by_id",
            json={"institution_id": "ins_test", "country_codes": ["US"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "institution" in data
        assert "request_id" in data

        institution = data["institution"]
        assert institution["institution_id"] == "ins_test"
        assert institution["name"] == "DoppelBank"
        assert institution["country_codes"] == ["US"]
        assert institution["url"] == "https://doppelbank.com"
        assert institution["primary_color"] == "#003d6b"
        assert institution["oauth"] is True
        assert "auth" in institution["products"]
        assert "transactions" in institution["products"]

        # Logo should be present as raw base64 string (152x152 PNG per Plaid spec)
        assert institution["logo"] is not None
        assert isinstance(institution["logo"], str)
        assert len(institution["logo"]) > 100  # Should be a substantial base64 string
        # Verify it's valid base64 by trying to decode it
        import base64

        try:
            base64.b64decode(institution["logo"])
        except Exception as e:
            raise AssertionError("Logo should be valid base64 string") from e
