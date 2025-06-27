"""
API endpoints for fetching account information.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException

from doppelbank.lib.ids import AccountId
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
    account_id = request.access_token.split("|")[0]

    # Read account data to validate it exists
    read_account_data(account_id)

    # Try to parse hierarchical account ID for richer metadata
    try:
        parsed_account = AccountId.from_wire(account_id)
        institution_id = parsed_account.institution_id
        account_name = (
            f"{parsed_account.persona_id.title()} {parsed_account.account_type.title()}"
        )
        item_id = parsed_account.item_id.to_wire()
    except Exception:
        # Fall back to simple account info
        institution_id = "doppelbank"
        account_name = f"Account {account_id}"
        item_id = f"{account_id}|item"

    accounts = [
        Account(
            account_id=account_id,
            balances=Balance(
                available=100.0,
                current=110.0,
                iso_currency_code="USD",
            ),
            name=account_name,
            mask="1111",
            type="depository",
            subtype="checking",
        )
    ]

    item = Item(
        item_id=item_id,
        institution_id=institution_id,
        webhook="",
    )

    return AccountsGetResponse(
        accounts=accounts,
        item=item,
        request_id=str(uuid.uuid4()),
    )
