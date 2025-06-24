import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException

from generated.detritus import BankLedger

app = FastAPI()


def get_data_dir() -> Path:
    """Get the data directory, configurable via environment variable."""
    data_dir = Path(
        os.environ.get("VENEER_DATA_DIR", Path(os.path.dirname(__file__)) / "data")
    )
    data_dir.mkdir(exist_ok=True)
    return data_dir


# TODO: Add authentication
# TODO: Support more endpoints (e.g., /accounts, /balances)


@app.get("/transactions/sync")
# TODO: Transform BankLedger to Plaid API format before returning (not the real Plaid format)
# TODO: Always serve as JSON (this is fake-Plaid, not a real protobuf API)
# TODO: Accept a timestamp query param (e.g., 'as_of') to support Plaid-style sync semantics
# TODO: Use account_id (not filename) to select the ledger file; map account_id to file internally
# TODO: Remove 'format' param, only support JSON
# TODO: Remove 'file' param, only support account_id
# TODO: Add proper error handling for missing/invalid account_id
# TODO: Add tests for Plaid-style sync behavior
# TODO: Document all API quirks and differences from real Plaid


def transactions_sync(file: str = "test_ledger_detritus.json", format: str = "json"):
    """Serve transactions from a detritus ledger file in the data directory."""
    data_dir = get_data_dir()
    ledger_path = data_dir / file
    if not ledger_path.exists():
        raise HTTPException(status_code=404, detail="Ledger file not found")
    # Linter workaround: use BankLedger.from_json and .parse for binary
    if format == "json":
        with open(ledger_path, "r") as f:
            ledger = BankLedger().from_json(f.read())
    elif format == "binary":
        with open(ledger_path, "rb") as f:
            ledger = BankLedger()
            ledger.parse(f.read())
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
    return ledger.to_dict()


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
