import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

import msgspec
from fastapi import APIRouter, HTTPException

from doppelbank.lib.ids import AccountId, ItemId
from doppelbank.schemas.detritus import AddCleared, AddPending, BankLedger
from doppelbank.veneer.models import (
    Account,
    Balance,
    Location,
    PaymentMeta,
    PersonalFinanceCategory,
    Transaction,
    TransactionsSyncRequest,
    TransactionsSyncResponse,
)
from doppelbank.veneer.utils import find_account_file

router: APIRouter = APIRouter()

logger = logging.getLogger(__name__)


def validate_account_id(account_id: str) -> None:
    """Validate account_id to prevent directory traversal and other security issues."""
    # For hierarchical IDs, allow hyphens as delimiters
    if not re.match(r"^[a-zA-Z0-9_-]{1,128}$", account_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Account ID must be 1-128 characters and can only contain letters, "
                "numbers, underscores, and hyphens"
            ),
        )


def transform_ledger_to_plaid(
    ledger: BankLedger, account_id: str, cursor: str | None = None
) -> TransactionsSyncResponse:
    """Transform a BankLedger to Plaid-style sync response."""

    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Use cursor as next_cursor, or current timestamp if not provided
    next_cursor = cursor or datetime.now().isoformat()

    # Create account with dummy balance (in real implementation, this would come from
    # balance events)
    dummy_balance = Balance(
        available=1000.0,
        current=1000.0,
        iso_currency_code="USD",
        unofficial_currency_code=None,
        limit=None,
    )

    # Parse hierarchical account ID for metadata
    parsed_account = AccountId.from_wire(account_id)
    account_name = f"{parsed_account.persona_id.title()} {parsed_account.account_type.title()}"
    account_subtype = (
        "checking"
        if parsed_account.account_type in ["checking", "chequing"]
        else parsed_account.account_type
    )

    account = Account(
        account_id=account_id,
        balances=dummy_balance,
        name=account_name,
        mask="1111",
        type="depository",
        subtype=account_subtype,
    )

    # Transform detritus events to Plaid transactions
    transactions = []
    for bank_event in ledger.events:
        # Check event type using isinstance with Tagged unions
        ev: AddCleared | AddPending | None = None
        is_pending = False

        if isinstance(bank_event.event, AddCleared):
            ev = bank_event.event
            is_pending = False
        elif isinstance(bank_event.event, AddPending):
            ev = bank_event.event
            is_pending = True

        if ev is not None:
            transaction = Transaction(
                transaction_id=ev.transaction_id,
                account_id=ev.account_id,
                amount=ev.amount / 100.0,  # Convert cents to dollars
                date=bank_event.timestamp.split("T")[0],  # Extract date part from event timestamp
                name=ev.description,
                merchant_name=ev.merchant,
                personal_finance_category=PersonalFinanceCategory(
                    primary=ev.category, detailed=ev.category, confidence_level="high"
                ),
                pending=is_pending,
                location=Location(),
                payment_meta=PaymentMeta(),
                payment_channel="in_store",
                transaction_type="place",
                iso_currency_code="USD",
                authorized_date=bank_event.timestamp.split("T")[0],
                authorized_datetime=bank_event.timestamp,
                datetime=bank_event.timestamp,
                counterparties=[],
                personal_finance_category_icon_url=None,
                transaction_code=None,
            )
            transactions.append(transaction)

    return TransactionsSyncResponse(
        accounts=[account],
        added=transactions,
        modified=[],
        removed=[],
        next_cursor=next_cursor,
        has_more=False,
        request_id=request_id,
    )


def account_ids_from_access_token(access_token: str) -> list[str]:
    """Extract account IDs from access token using hierarchical structure."""
    # Parse the access token to get the item ID
    item_id = ItemId.from_access_token(access_token)

    # Scan for all accounts under this item
    account_ids = []
    personas_dir = Path("data/personas")
    persona_institution_dir = personas_dir / item_id.persona_id / item_id.institution_id

    if not persona_institution_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Persona {item_id.persona_id} not found",
        )

    for account_file in persona_institution_dir.glob("*.json"):
        account_type = account_file.stem
        account_id = f"{item_id.to_wire()}-{account_type}"
        account_ids.append(account_id)

    return account_ids


def handle_transactions_sync(
    request: TransactionsSyncRequest,
) -> TransactionsSyncResponse:
    """Handle transactions sync request and return Plaid-style response."""
    account_ids = account_ids_from_access_token(request.access_token)

    # If account_id is provided, filter to only that account
    if request.options and "account_id" in request.options:
        if request.options["account_id"] not in account_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Account ID {request.options['account_id']} not found",
            )
        account_ids = [request.options["account_id"]]

    for account_id in account_ids:
        validate_account_id(account_id)

    cursor = request.cursor

    if len(account_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail=("Zero or multiple account IDs providedbut only exactly one is supported"),
        )

    account_id = account_ids[0]
    ledger_path = find_account_file(account_id)

    if not ledger_path.exists():
        logger.error(f"Ledger file not found for account {account_id} (looked in {ledger_path})")
        raise HTTPException(
            status_code=404,
            detail=f"Ledger file not found for account {account_id}",
        )

    with open(ledger_path, "rb") as f:
        ledger = msgspec.json.decode(f.read(), type=BankLedger)

    return transform_ledger_to_plaid(ledger, account_id, cursor)


@router.post("/transactions/sync", response_model=TransactionsSyncResponse)
def transactions_sync(request: TransactionsSyncRequest) -> TransactionsSyncResponse:
    return handle_transactions_sync(request)
