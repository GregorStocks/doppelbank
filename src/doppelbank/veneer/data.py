import logging
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

logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    return Path(os.environ.get("VENEER_DATA_DIR", "data"))


def find_account_file(account_id: AccountId) -> Path:
    # First try hierarchical structure
    account_file = (
        get_data_dir()
        / "personas"
        / account_id.persona_id
        / account_id.institution_id
        / f"{account_id.account_type}.json"
    )
    return account_file


def read_account_data(account_id: AccountId) -> BankLedger:
    file_path = find_account_file(account_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Account '{account_id.to_wire()}' not found")
    return load_json(file_path, BankLedger)


def get_accounts(item_id: ItemId) -> list[Account]:
    """Get all accounts for an item."""
    institution_id = item_id.institution_id
    persona_id = item_id.persona_id

    accounts = []
    persona_institution_dir = get_data_dir() / "personas" / persona_id / institution_id

    if not persona_institution_dir.exists():
        logger.warning(f"Couldn't find account file in {persona_institution_dir}")
        raise HTTPException(status_code=404, detail=f"Persona {item_id.persona_id} not found")

    for account_file in persona_institution_dir.glob("*.json"):
        account_type = account_file.stem  # e.g., "checking", "savings"
        account_id = AccountId(
            user_id=item_id.user_id,
            persona_id=persona_id,
            institution_id=institution_id,
            account_type=account_type,
        )

        # Read account data to get balance information

        read_account_data(account_id)  # Validate account exists
        # Calculate current balance from events (simplified)
        current_balance = 1000.0  # Default
        available_balance = 1000.0  # Default

        account_name = f"{persona_id.title()} {account_type.title()}"
        account_subtype = "checking" if account_type in ["checking", "chequing"] else account_type

        accounts.append(
            Account(
                account_id=account_id.to_wire(),
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


def get_available_personas() -> list[str]:
    """Get list of available personas from data directory."""
    personas_dir = get_data_dir() / "personas"
    if not personas_dir.exists():
        raise ValueError("No personas found")
    return [p.name for p in personas_dir.iterdir() if p.is_dir()]


def get_available_institutions_for_persona(persona_id: str) -> list[str]:
    """Get list of institutions available for a given persona."""
    persona_dir = get_data_dir() / "personas" / persona_id
    if not persona_dir.exists():
        raise ValueError("Persona not found")
    return [inst.name for inst in persona_dir.iterdir() if inst.is_dir()]
