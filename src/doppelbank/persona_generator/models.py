"""
Data models for bedrock financial events using msgspec.

This module provides utilities for working with msgspec event classes
and core event creation functions.
"""

import uuid

from doppelbank.schemas.bedrock import CardSwipeEvent, Event, PaycheckEvent


def create_paycheck_event(
    amount: int,  # int cents
    timestamp: str,
    employer: str,
    description: str = "Bi-weekly paycheck",
) -> Event:
    """Create a paycheck event. Amount is int cents."""
    return PaycheckEvent(
        event_id=str(uuid.uuid4()),
        amount=amount,
        timestamp=timestamp,
        employer=employer,
        description=description,
    )


def create_card_swipe_event(
    amount: int,  # int cents
    timestamp: str,
    merchant: str,
    category: str,
    description: str = "",
) -> Event:
    """Create a card swipe event. Amount is int cents."""
    return CardSwipeEvent(
        event_id=str(uuid.uuid4()),
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
        elif isinstance(event, CardSwipeEvent):
            summary["card_swipe"] += 1

    return summary
