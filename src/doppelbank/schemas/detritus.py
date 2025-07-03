"""
Detritus data structures using msgspec.

These replace the protobuf definitions in detritus.proto.
"""

import msgspec


class AddPending(msgspec.Struct, tag="add_pending"):
    """A pending transaction is added."""

    event_id: str
    transaction_id: str
    # Amount in integer cents (e.g., USD 12.34 = 1234). Positive = credit to
    # account, negative = debit from account.
    amount: int
    description: str
    merchant: str
    category: str


class RemovePending(msgspec.Struct, tag="remove_pending"):
    """A pending transaction is removed (e.g., when it clears)."""

    event_id: str
    transaction_id: str
    reason: str
    related_event_id: str


class AddCleared(msgspec.Struct, tag="add_cleared"):
    """A cleared transaction is added."""

    event_id: str
    transaction_id: str
    amount: int
    description: str
    merchant: str
    category: str
    pending_event_id: str


class UpdateBalance(msgspec.Struct, tag="update_balance"):
    """The available balance is updated."""

    event_id: str
    new_balance: int
    reason: str
    related_event_id: str


# Tagged union for event data
EventData = AddPending | RemovePending | AddCleared | UpdateBalance


class BankEvent(msgspec.Struct):
    """Atomic bank ledger event."""

    event_id: str
    # Timestamp in UTC, ISO8601 format with microsecond precision (e.g.,
    # 2024-07-01T12:00:00.123456Z). All timestamps in this schema use this format
    # and precision. If multiple events have the same timestamp, they are
    # considered to have occurred simultaneously.
    timestamp: str
    event: EventData


class BankLedger(msgspec.Struct):
    """Collection of bank events."""

    events: list[BankEvent]
