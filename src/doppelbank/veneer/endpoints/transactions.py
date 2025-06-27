import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

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
from doppelbank.veneer.utils import get_data_dir
from generated.detritus import BankLedger

router: APIRouter = APIRouter()

logger = logging.getLogger(__name__)


def validate_account_id(account_id: str) -> None:
    """Validate account_id to prevent directory traversal and other security issues."""
    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", account_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Account ID must be 1-64 characters and can only contain letters, "
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
    account = Account(
        account_id=account_id,
        balances=dummy_balance,
        name=f"Account {account_id}",
        mask="1111",
        type="depository",
        subtype="checking",
    )

    # Transform detritus events to Plaid transactions
    transactions = []
    for event in ledger.events:
        ev = None
        if (event.add_cleared and event.add_cleared.account_id == account_id):
            ev = event.add_cleared
        elif (
            event.add_pending and event.add_pending.account_id == account_id
        ):
            ev = event.add_pending
            # Convert cleared transaction
        else:
            continue
        transaction = Transaction(
                transaction_id=ev.transaction_id,
                account_id=ev.account_id,
                amount=ev.amount / 100.0,  # Convert cents to dollars
                date=event.timestamp.split("T")[
                    0
                ],  # Extract date part from event timestamp
                name=ev.description,
                merchant_name=ev.merchant,
                personal_finance_category=PersonalFinanceCategory(
                    primary=ev.category, detailed=ev.category, confidence_level="high"
                ),
                pending=bool(event.add_pending and event.add_pending.account_id),
                location=Location(),
                payment_meta=PaymentMeta(),
                payment_channel="in_store",
                transaction_type="place",
                iso_currency_code="USD",
                authorized_date=event.timestamp.split("T")[0],
                authorized_datetime=event.timestamp,
                datetime=event.timestamp,
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
    return [re.sub("[|].*", "", access_token)]


def handle_transactions_sync(
    request: TransactionsSyncRequest, data_dir: Path
) -> TransactionsSyncResponse:
    """Handle transactions sync request and return Plaid-style response."""
    account_ids = account_ids_from_access_token(request.access_token)

    # If account_id is provided, filter to only that account
    if request.options and "account_id" in request.options:
        account_ids = list(
            set.intersection(set(account_ids), {request.options["account_id"]})
        )

    for account_id in account_ids:
        validate_account_id(account_id)

    cursor = request.cursor

    if len(account_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "Zero or multiple account IDs provided"
                "but only exactly one is supported"
            ),
        )

    account_id = account_ids[0]
    filename = f"{account_id}.json"
    ledger_path = data_dir / filename

    if not ledger_path.exists():
        logger.error(
            f"Ledger file not found for account {account_id} (looked in {ledger_path})"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Ledger file not found for account {account_id}",
        )

    with open(ledger_path) as f:
        ledger = BankLedger().from_json(f.read())

    return transform_ledger_to_plaid(ledger, account_id, cursor)


@router.post("/transactions/sync", response_model=TransactionsSyncResponse)
def transactions_sync(request: TransactionsSyncRequest) -> TransactionsSyncResponse:
    data_dir = get_data_dir()
    return handle_transactions_sync(request, data_dir)
