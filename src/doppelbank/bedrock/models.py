"""
Data models for bedrock financial events using protobuf.

This module provides utilities for working with protobuf-generated event classes
and core event creation functions.
"""

import betterproto

from generated.bedrock import CardSwipeEvent, Event, PaycheckEvent, TransferEvent


def create_paycheck_event(
    user_id: str,
    account_id: str,
    amount: int,  # int cents
    timestamp: str,
    employer: str,
    description: str = "Bi-weekly paycheck",
) -> Event:
    """Create a paycheck event. Amount is int cents."""
    event = Event()
    event.paycheck = PaycheckEvent(
        event_id="",  # can be set by caller if needed
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        timestamp=timestamp,
        employer=employer,
        description=description,
    )
    return event


def create_transfer_event(
    user_id: str,
    amount: int,  # int cents
    timestamp: str,
    from_account: str,
    to_account: str,
    description: str = "",
) -> Event:
    """Create a transfer event. Amount is int cents."""
    event = Event()
    event.transfer = TransferEvent(
        event_id="",
        user_id=user_id,
        amount=amount,
        timestamp=timestamp,
        from_account=from_account,
        to_account=to_account,
        description=description or f"Transfer from {from_account} to {to_account}",
    )
    return event


def create_card_swipe_event(
    user_id: str,
    account_id: str,
    amount: int,  # int cents
    timestamp: str,
    merchant: str,
    category: str,
    description: str = "",
) -> Event:
    """Create a card swipe event. Amount is int cents."""
    event = Event()
    event.card_swipe = CardSwipeEvent(
        event_id="",
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        timestamp=timestamp,
        merchant=merchant,
        category=category,
        description=description or f"Purchase at {merchant}",
    )
    return event


def get_event_summary(events: list[Event]) -> dict:
    """Get a summary of event types and counts."""
    summary = {"paycheck": 0, "transfer": 0, "card_swipe": 0, "total": len(events)}

    for event in events:
        field_name, _ = betterproto.which_one_of(event, "event_data")
        if field_name:
            summary[field_name] += 1

    return summary
