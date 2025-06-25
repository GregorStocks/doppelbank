import os
import re
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from generated.detritus import BankLedger

app = FastAPI()


def get_data_dir() -> Path:
    """Get the data directory, configurable via environment variable."""
    data_dir = Path(
        os.environ.get("VENEER_DATA_DIR", Path(os.path.dirname(__file__)) / "data")
    )
    data_dir.mkdir(exist_ok=True)
    return data_dir


def validate_account_id(account_id: str) -> None:
    """Validate account_id to prevent directory traversal and other security issues."""
    if not account_id:
        raise HTTPException(status_code=400, detail="Account ID cannot be empty")

    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", account_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Account ID must be 1-64 characters and can only contain letters, "
                "numbers, underscores, and hyphens"
            ),
        )


class TransactionsSyncOptions(BaseModel):
    account_id: Optional[str] = None


class TransactionsSyncRequest(BaseModel):
    options: Optional[TransactionsSyncOptions] = None


# TODO: Support more endpoints (e.g., /accounts, /balances)


@app.post("/transactions/sync")
# TODO: Transform BankLedger to Plaid API format before returning (not the real Plaid format)
# TODO: Accept a timestamp query param (e.g., 'as_of') to support Plaid-style sync semantics
# TODO: Add tests for Plaid-style sync behavior
# TODO: Document all API quirks and differences from real Plaid


def transactions_sync(request: TransactionsSyncRequest) -> Any:
    """Serve transactions from a detritus ledger file for the given account_id."""
    if not (request.options and request.options.account_id is not None):
        raise HTTPException(status_code=400, detail="account_id must be provided")
    account_id = request.options.account_id

    # Validate account_id for security
    validate_account_id(account_id)

    # Construct filename from account_id
    filename = f"{account_id}.json"
    data_dir = get_data_dir()
    ledger_path = data_dir / filename
    if not ledger_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Ledger file not found for account {account_id}"
        )

    with open(ledger_path, "r") as f:
        ledger = BankLedger().from_json(f.read())
    return ledger.to_dict()


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
