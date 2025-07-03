"""
API endpoints for fetching account information.
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from doppelbank.lib.ids import ItemId
from doppelbank.lib.serde import load_json
from doppelbank.schemas.detritus import BankLedger
from doppelbank.veneer.models import (
    Account,
    AccountsGetRequest,
    AccountsGetResponse,
    Balance,
    Item,
)
from doppelbank.veneer.utils import find_account_file

logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


def read_account_data(account_id: str) -> BankLedger:
    """Read account data using hierarchical or flat file structure."""
    file_path = find_account_file(account_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return load_json(file_path, BankLedger)


@router.post("/accounts/get")
def accounts_get(request: AccountsGetRequest) -> AccountsGetResponse:
    """Handle /accounts/get endpoint."""
    # Extract item_id from access_token using helper method
    item_id = ItemId.from_access_token(request.access_token)
    institution_id = item_id.institution_id
    persona_id = item_id.persona_id

    # Scan for all accounts under this persona/institution
    accounts = []
    persona_institution_dir = Path("data/personas") / persona_id / institution_id
    if persona_institution_dir.exists():
        for account_file in persona_institution_dir.glob("*.json"):
            account_type = account_file.stem  # e.g., "checking", "savings"
            account_id = f"{item_id.to_wire()}-{account_type}"

            # Read account data to get balance information

            read_account_data(account_id)  # Validate account exists
            # Calculate current balance from events (simplified)
            current_balance = 1000.0  # Default
            available_balance = 1000.0  # Default

            account_name = f"{persona_id.title()} {account_type.title()}"
            account_subtype = (
                "checking" if account_type in ["checking", "chequing"] else account_type
            )

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

    item = Item(
        item_id=item_id.to_wire(),
        institution_id=institution_id,
        webhook="",
    )

    return AccountsGetResponse(
        accounts=accounts,
        item=item,
        request_id=str(uuid.uuid4()),
    )
