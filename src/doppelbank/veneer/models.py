from typing import Any

from doppelbank.veneer.common import VeneerRequest, VeneerResponse


class AccountsGetRequest(VeneerRequest):
    access_token: str
    options: dict[str, Any] | None = None


class Balance(VeneerResponse):
    available: float | None = None
    current: float
    iso_currency_code: str
    unofficial_currency_code: str | None = None
    limit: float | None = None


class Account(VeneerResponse):
    account_id: str
    balances: Balance
    name: str
    mask: str | None = None
    type: str
    subtype: str | None = None
    verification_status: str | None = None
    persistent_account_id: str | None = None


class Item(VeneerResponse):
    item_id: str
    institution_id: str | None = None
    webhook: str | None = None


class AccountsGetResponse(VeneerResponse):
    accounts: list[Account]
    item: Item
    request_id: str


class TransactionsSyncRequest(VeneerRequest):
    access_token: str
    cursor: str | None = None
    count: int = 100
    options: dict[str, Any] | None = None


class Transaction(VeneerResponse):
    transaction_id: str
    account_id: str
    amount: float
    iso_currency_code: str | None = None
    unofficial_currency_code: str | None = None
    category: list[str] | None = None
    category_id: str | None = None
    check_number: str | None = None
    date: str
    location: dict[str, Any]
    name: str
    merchant_name: str | None = None
    original_description: str | None = None
    payment_meta: dict[str, Any]
    payment_channel: str
    pending: bool
    pending_transaction_id: str | None = None
    account_owner: str | None = None
    transaction_type: str
    logo_url: str | None = None
    authorized_date: str | None = None
    authorized_datetime: str | None = None
    datetime: str | None = None


class TransactionsSyncResponse(VeneerResponse):
    accounts: list[Account]
    added: list[Transaction]
    modified: list[Transaction]
    removed: list[dict[str, Any]]
    next_cursor: str
    has_more: bool
    request_id: str
