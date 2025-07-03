import logging
import uuid
from datetime import datetime

import msgspec
from fastapi import APIRouter, HTTPException

from doppelbank.lib.ids import AccountId, ItemId
from doppelbank.schemas.detritus import AddCleared, AddPending, BankLedger
from doppelbank.veneer.data import find_account_file, get_data_dir
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

router: APIRouter = APIRouter()

logger = logging.getLogger(__name__)


def transform_ledger_to_plaid(
    ledger: BankLedger, account_id: AccountId, cursor: str | None = None
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
    account_name = f"{account_id.persona_id.title()} {account_id.account_type.title()}"

    account = Account(
        account_id=account_id.to_wire(),
        balances=dummy_balance,
        name=account_name,
        mask="1111",
        type="depository",
        subtype=account_id.account_type,
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
                account_id=account_id.to_wire(),
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


def account_ids_from_access_token(access_token: str) -> list[AccountId]:
    """Extract account IDs from access token using hierarchical structure."""
    # Parse the access token to get the item ID
    item_id = ItemId.from_access_token(access_token)

    # Scan for all accounts under this item
    personas_dir = get_data_dir() / "personas"
    persona_institution_dir = personas_dir / item_id.persona_id / item_id.institution_id

    if not persona_institution_dir.exists():
        logger.error(f"Couldn't find persona dir {persona_institution_dir}")
        raise HTTPException(
            status_code=404,
            detail=f"Persona {item_id.persona_id} not found",
        )

    account_ids = []
    for account_file in persona_institution_dir.glob("*.json"):
        account_type = account_file.stem
        account_id = AccountId(
            user_id=item_id.user_id,
            persona_id=item_id.persona_id,
            institution_id=item_id.institution_id,
            account_type=account_type,
        )
        account_ids.append(account_id)

    return account_ids


def handle_transactions_sync(
    request: TransactionsSyncRequest,
) -> TransactionsSyncResponse:
    """Handle transactions sync request and return Plaid-style response."""
    account_ids = account_ids_from_access_token(request.access_token)

    # If account_id is provided, filter to only that account
    if request.options and "account_id" in request.options:
        account_id = AccountId.from_wire(request.options["account_id"])
        if account_id not in account_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Account ID {request.options['account_id']} not found",
            )
        account_ids = [account_id]

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
