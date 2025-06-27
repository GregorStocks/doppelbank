"""
Bedrock data structures using msgspec.

These replace the protobuf definitions in bedrock.proto.
"""

import msgspec


class PaycheckEvent(msgspec.Struct, tag="paycheck"):
    """A paycheck event representing regular income from employment."""

    event_id: str
    user_id: str
    # Timestamp in UTC, ISO8601 format with microsecond precision (e.g.,
    # 2024-07-01T12:00:00.123456Z). All timestamps in this schema use this format
    # and precision.
    timestamp: str
    # Amount in integer cents (e.g., USD 12.34 = 1234). Positive = credit to
    # account, negative = debit from account.
    amount: int
    employer: str
    description: str
    account_id: str


class TransferEvent(msgspec.Struct, tag="transfer"):
    """A transfer event representing money movement between accounts."""

    event_id: str
    user_id: str
    timestamp: str
    amount: int
    from_account: str
    to_account: str
    description: str


class CardSwipeEvent(msgspec.Struct, tag="card_swipe"):
    """A card swipe event representing credit/debit card transactions."""

    event_id: str
    user_id: str
    timestamp: str
    amount: int
    merchant: str
    category: str
    description: str
    account_id: str


# Tagged union for events
Event = PaycheckEvent | TransferEvent | CardSwipeEvent


class EventCollection(msgspec.Struct):
    """A collection of events."""

    events: list[Event]
