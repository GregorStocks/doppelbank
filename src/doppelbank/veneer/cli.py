from fastapi import FastAPI, HTTPException
from pathlib import Path
from doppelbank.lib import serde
from generated.detritus import BankLedger
import os

app = FastAPI()

DATA_DIR = Path(os.path.dirname(__file__)) / "data"
DATA_DIR.mkdir(exist_ok=True)

# TODO: Add authentication
# TODO: Support more endpoints (e.g., /accounts, /balances)

@app.get("/transactions/sync")
# TODO: Transform BankLedger to Plaid API format before returning (this is not the real Plaid format)
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
    ledger_path = DATA_DIR / file
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
    print("hello, veneer")


if __name__ == "__main__":
    main()
