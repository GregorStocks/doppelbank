import os
from pathlib import Path

from fastapi import HTTPException

from doppelbank.lib.ids import AccountId, ItemId
from doppelbank.lib.serde import load_json
from doppelbank.schemas.detritus import BankLedger
from doppelbank.veneer.models import (
    Account,
    Balance,
)


def get_data_dir() -> Path:
    """Get the data directory, configurable via environment variable."""
    data_dir = Path(os.environ.get("VENEER_DATA_DIR", "tests/data/detritus"))
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_hierarchical_data_dir() -> Path:
    """Get the hierarchical data directory."""
    return Path(os.environ.get("VENEER_HIERARCHICAL_DATA_DIR", "data"))


def find_account_file(account_id: str) -> Path:
    """Find account data file using hierarchical ID structure or fallback to flat structure."""
    # First try hierarchical structure
    try:
        hierarchical_root = get_hierarchical_data_dir()
        if hierarchical_root.exists():
            # Try to parse as hierarchical account ID
            try:
                parsed_account = AccountId.from_wire(account_id)
                account_file = (
                    hierarchical_root
                    / "personas"
                    / parsed_account.persona_id
                    / parsed_account.institution_id
                    / f"{parsed_account.account_type}.json"
                )
                if account_file.exists():
                    return account_file
            except Exception:
                pass  # Fall through to flat structure search

            # Search in hierarchical structure for exact match
            personas_dir = hierarchical_root / "personas"
            if personas_dir.exists():
                for persona_dir in personas_dir.iterdir():
                    if persona_dir.is_dir():
                        for institution_dir in persona_dir.iterdir():
                            if institution_dir.is_dir():
                                for account_file in institution_dir.glob("*.json"):
                                    # Check if this file contains the account ID we're looking for
                                    try:
                                        with open(account_file) as f:
                                            content = f.read()
                                            if f'"account_id": "{account_id}"' in content:
                                                return account_file
                                    except Exception:
                                        continue
    except Exception:
        pass
    # Fall back to flat structure
    flat_data_dir = get_data_dir()
    flat_file = flat_data_dir / f"{account_id}.json"
    return flat_file


def read_account_data(account_id: str) -> BankLedger:
    """Read account data using hierarchical or flat file structure."""
    file_path = find_account_file(account_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return load_json(file_path, BankLedger)


def get_accounts(item_id: ItemId) -> list[Account]:
    """Get all accounts for an item."""
    institution_id = item_id.institution_id
    persona_id = item_id.persona_id

    accounts = []
    persona_institution_dir = Path("data/personas") / persona_id / institution_id
    if not persona_institution_dir.exists():
        raise HTTPException(status_code=404, detail=f"Persona {item_id.persona_id} not found")

    for account_file in persona_institution_dir.glob("*.json"):
        account_type = account_file.stem  # e.g., "checking", "savings"
        account_id = f"{item_id.to_wire()}-{account_type}"

        # Read account data to get balance information

        read_account_data(account_id)  # Validate account exists
        # Calculate current balance from events (simplified)
        current_balance = 1000.0  # Default
        available_balance = 1000.0  # Default

        account_name = f"{persona_id.title()} {account_type.title()}"
        account_subtype = "checking" if account_type in ["checking", "chequing"] else account_type

        accounts.append(
            Account(
                account_id=account_id,
                balances=Balance(
                    available=available_balance,
                    current=current_balance,
                    iso_currency_code="USD",
                ),
                name=account_name,
                mask="1111",
                type="depository",
                subtype=account_subtype,
            )
        )
    return accounts
