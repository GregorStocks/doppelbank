"""
API endpoints for fetching account information.
"""

import logging
import uuid

from fastapi import APIRouter

from doppelbank.lib.ids import ItemId
from doppelbank.veneer.data import get_accounts
from doppelbank.veneer.models import (
    AccountsGetRequest,
    AccountsGetResponse,
    Item,
)

logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/accounts/get")
def accounts_get(request: AccountsGetRequest) -> AccountsGetResponse:
    """Handle /accounts/get endpoint."""
    # Extract item_id from access_token using helper method
    item_id = ItemId.from_access_token(request.access_token)
    institution_id = item_id.institution_id

    accounts = get_accounts(item_id)

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
