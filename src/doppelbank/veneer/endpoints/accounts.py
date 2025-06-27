"""
API endpoints for fetching account information.
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from doppelbank.lib.serde import load_json
from doppelbank.schemas.detritus import BankLedger
from doppelbank.veneer.models import (
    Account,
    AccountsGetRequest,
    AccountsGetResponse,
    Balance,
    Item,
)
from doppelbank.veneer.utils import get_data_dir

logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


def read_account_data(account_id: str, data_dir: Path) -> BankLedger:
    """Read account data from the configured data directory."""
    file_path = data_dir / f"{account_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return load_json(file_path, BankLedger)


@router.post("/accounts/get")
def accounts_get(request: AccountsGetRequest) -> AccountsGetResponse:
    """Handle /accounts/get endpoint."""
    account_id = request.access_token.split("|")[0]
    # TODO: unify with access token/account id handling in transactions sync
    data_dir = get_data_dir()
    read_account_data(account_id, data_dir)
    # TODO: actually do something with the account data...

    accounts = [
        Account(
            account_id=account_id,
            balances=Balance(
                available=100.0,
                current=110.0,
                iso_currency_code="USD",
            ),
            name=f"Account {account_id}",
            mask="1111",
            type="depository",
            subtype="checking",
        )
    ]

    item = Item(
        item_id=f"{account_id}|123",
        institution_id="default_institution_id",
        webhook="",
    )

    return AccountsGetResponse(
        accounts=accounts,
        item=item,
        request_id=str(uuid.uuid4()),
    )
