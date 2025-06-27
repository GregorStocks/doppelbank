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


class Counterparty(VeneerResponse):
    name: str
    type: str
    logo_url: str | None = None
    website: str | None = None
    entity_id: str
    confidence_level: str


class Location(VeneerResponse):
    address: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    lat: float | None = None
    lon: float | None = None
    store_number: str | None = None


class PaymentMeta(VeneerResponse):
    by_order_of: str | None = None
    payee: str | None = None
    payer: str | None = None
    payment_method: str | None = None
    payment_processor: str | None = None
    ppd_id: str | None = None
    reason: str | None = None
    reference_number: str | None = None


class PersonalFinanceCategory(VeneerResponse):
    primary: str
    detailed: str
    confidence_level: str


class Transaction(VeneerResponse):
    account_id: str
    account_owner: str | None = None
    amount: float
    iso_currency_code: str
    unofficial_currency_code: str | None = None
    check_number: str | None = None
    counterparties: list[Counterparty]
    date: str
    datetime: str
    authorized_date: str
    authorized_datetime: str
    location: Location
    name: str
    merchant_name: str
    merchant_entity_id: str | None = None
    logo_url: str | None = None
    website: str | None = None
    payment_meta: PaymentMeta
    payment_channel: str | None = None
    pending: bool
    pending_transaction_id: str | None = None
    personal_finance_category: PersonalFinanceCategory
    personal_finance_category_icon_url: str | None = None
    transaction_id: str
    transaction_code: str | None = None
    transaction_type: str


class TransactionsSyncResponse(VeneerResponse):
    accounts: list[Account]
    added: list[Transaction]
    modified: list[Transaction]
    removed: list[dict[str, Any]]
    next_cursor: str
    has_more: bool
    request_id: str
