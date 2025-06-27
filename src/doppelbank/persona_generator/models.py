"""
Data models for bedrock financial events using msgspec.

This module provides utilities for working with msgspec event classes
and core event creation functions.
"""

from doppelbank.schemas.bedrock import (
    CardSwipeEvent,
    Event,
    PaycheckEvent,
    TransferEvent,
)


def create_paycheck_event(
    account_id: str,
    amount: int,  # int cents
    timestamp: str,
    employer: str,
    description: str = "Bi-weekly paycheck",
) -> Event:
    """Create a paycheck event. Amount is int cents."""
    return PaycheckEvent(
        event_id="",  # can be set by caller if needed
        user_id="",  # derived from account_id when needed
        account_id=account_id,
        amount=amount,
        timestamp=timestamp,
        employer=employer,
        description=description,
    )


def create_transfer_event(
    amount: int,  # int cents
    timestamp: str,
    from_account: str,
    to_account: str,
    description: str = "",
) -> Event:
    """Create a transfer event. Amount is int cents."""
    return TransferEvent(
        event_id="",
        user_id="",  # derived from account_id when needed
        amount=amount,
        timestamp=timestamp,
        from_account=from_account,
        to_account=to_account,
        description=description or f"Transfer from {from_account} to {to_account}",
    )


def create_card_swipe_event(
    account_id: str,
    amount: int,  # int cents
    timestamp: str,
    merchant: str,
    category: str,
    description: str = "",
) -> Event:
    """Create a card swipe event. Amount is int cents."""
    return CardSwipeEvent(
        event_id="",
        user_id="",  # derived from account_id when needed
        account_id=account_id,
        amount=amount,
        timestamp=timestamp,
        merchant=merchant,
        category=category,
        description=description or f"Purchase at {merchant}",
    )


def get_event_summary(events: list[Event]) -> dict:
    """Get a summary of event types and counts."""
    summary = {"paycheck": 0, "transfer": 0, "card_swipe": 0, "total": len(events)}

    for event in events:
        # Check event type using isinstance with Tagged unions
        if isinstance(event, PaycheckEvent):
            summary["paycheck"] += 1
        elif isinstance(event, TransferEvent):
            summary["transfer"] += 1
        elif isinstance(event, CardSwipeEvent):
            summary["card_swipe"] += 1

    return summary
