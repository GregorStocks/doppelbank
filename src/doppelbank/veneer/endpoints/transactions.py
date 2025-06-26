import re
import uuid
from datetime import datetime
from pathlib import Path

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from doppelbank.veneer.model import get_data_dir
from generated.detritus import BankLedger

router = APIRouter()

logger = logging.getLogger(__name__)


def validate_account_id(account_id: str) -> None:
    """Validate account_id to prevent directory traversal and other security issues."""
    if not account_id:
        raise HTTPException(status_code=400, detail="Account ID cannot be empty")

    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", account_id):
        raise HTTPException(
            status_code=400,
            detail=(
                "Account ID must be 1-64 characters and can only contain letters, "
                "numbers, underscores, and hyphens"
            ),
        )


class AccountBalance(BaseModel):
    available: float
    current: float
    iso_currency_code: str = "USD"
    unofficial_currency_code: str | None = None


class Account(BaseModel):
    account_id: str
    name: str
    balances: AccountBalance


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    amount: float
    date: str
    name: str
    merchant_name: str | None = None
    category: list[str] | None = None
    pending: bool = False


class TransactionsSyncOptions(BaseModel):
    account_id: str | None = None
    cursor: str | None = None


class TransactionsSyncRequest(BaseModel):
    access_token: str
    options: TransactionsSyncOptions | None = None


class PlaidSyncResponse(BaseModel):
    accounts: list[Account]
    added: list[Transaction]
    modified: list[Transaction] = []
    removed: list[Transaction] = []
    next_cursor: str
    has_more: bool = False
    request_id: str


def transform_ledger_to_plaid(
    ledger: BankLedger, account_id: str, cursor: str | None = None
) -> PlaidSyncResponse:
    """Transform a BankLedger to Plaid-style sync response."""

    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Use cursor as next_cursor, or current timestamp if not provided
    next_cursor = cursor or datetime.now().isoformat()

    # Create account with dummy balance (in real implementation, this would come from
    # balance events)
    account = Account(
        account_id=account_id,
        name=f"Account {account_id}",
        balances=AccountBalance(
            available=1000.0,  # Dummy balance
            current=1000.0,
        ),
    )

    # Transform detritus events to Plaid transactions
    transactions = []
    for event in ledger.events:
        if event.add_cleared:
            # Convert cleared transaction
            ac = event.add_cleared
            transaction = Transaction(
                transaction_id=ac.transaction_id,
                account_id=ac.account_id,
                amount=ac.amount / 100.0,  # Convert cents to dollars
                date=event.timestamp.split("T")[
                    0
                ],  # Extract date part from event timestamp
                name=ac.description or "Transaction",
                merchant_name=ac.merchant,
                category=[ac.category] if ac.category else None,
                pending=False,
            )
            transactions.append(transaction)
        elif event.add_pending:
            # Convert pending transaction
            ap = event.add_pending
            transaction = Transaction(
                transaction_id=ap.transaction_id,
                account_id=ap.account_id,
                amount=ap.amount / 100.0,  # Convert cents to dollars
                date=event.timestamp.split("T")[
                    0
                ],  # Extract date part from event timestamp
                name=ap.description or "Transaction",
                merchant_name=ap.merchant,
                category=[ap.category] if ap.category else None,
                pending=True,
            )
            transactions.append(transaction)

    return PlaidSyncResponse(
        accounts=[account],
        added=transactions,
        next_cursor=next_cursor,
        request_id=request_id,
    )


def account_ids_from_access_token(access_token: str) -> list[str]:
    return [access_token]


def handle_transactions_sync(
    request: TransactionsSyncRequest, data_dir: Path
) -> PlaidSyncResponse:
    """Handle transactions sync request and return Plaid-style response."""
    account_ids = account_ids_from_access_token(request.access_token)
    if request.options and request.options.account_id:
        account_ids = list(
            set.intersection(set(account_ids), {request.options.account_id})
        )

    for account_id in account_ids:
        validate_account_id(account_id)

    for account_id in account_ids:
        filename = f"{account_id}.json"
        ledger_path = data_dir / filename

    cursor = request.options.cursor if request.options else None

    # Construct filename from account_id
    filename = f"{account_id}.json"
    ledger_path = data_dir / filename
    if not ledger_path.exists():
        logger.error(f"Ledger file not found for account {account_id} (looked in {ledger_path})")
        raise HTTPException(
            status_code=404, detail=f"Ledger file not found for account {account_id}"
        )

    with open(ledger_path) as f:
        ledger = BankLedger().from_json(f.read())

    # Transform to Plaid format
    return transform_ledger_to_plaid(ledger, account_id, cursor)


@router.post("/transactions/sync")
def transactions_sync(request: TransactionsSyncRequest) -> PlaidSyncResponse:
    data_dir = get_data_dir()
    return handle_transactions_sync(request, data_dir)
