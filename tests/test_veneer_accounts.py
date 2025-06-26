"""
FastAPI TestClient tests for the Veneer API accounts endpoints.
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


class TestVeneerAccountsAPI:
    """Test the Veneer API accounts endpoints using FastAPI TestClient."""

    def test_accounts_get_basic(self) -> None:
        """Test basic accounts get endpoint using FastAPI TestClient."""
        client = TestClient(app)
        response = client.post(
            "/accounts/get",
            json={
                "access_token": "test_account|123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "accounts" in data
        assert "item" in data
        assert "request_id" in data
        assert isinstance(data["accounts"], list)
        assert len(data["accounts"]) > 0

        account = data["accounts"][0]
        assert "balances" in account
        assert "available" in account["balances"]
        assert "current" in account["balances"]
        assert "iso_currency_code" in account["balances"]
