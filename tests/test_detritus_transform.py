from doppelbank.detritus.transform import bedrock_to_detritus
from generated.bedrock import CardSwipeEvent, Event, EventCollection
from generated.detritus import (
    AddCleared,
    AddPending,
    BankEvent,
    BankLedger,
    RemovePending,
)


def test_bedrock_to_detritus_minimal():
    event = Event(
        card_swipe=CardSwipeEvent(
            event_id="evt1",
            user_id="u1",
            timestamp="2024-01-01T12:00:00.000000Z",
            amount=12345,  # int cents
            merchant="Test Merchant",
            category="Test Category",
            description="Test Desc",
        )
    )
    collection = EventCollection(events=[event])
    ledger = bedrock_to_detritus(collection)
    assert isinstance(ledger, BankLedger)
    assert len(ledger.events) == 3
    pending, cleared, remove_pending = ledger.events
    assert isinstance(pending, BankEvent)
    assert pending.add_pending is not None
    assert isinstance(pending.add_pending, AddPending)
    assert pending.add_pending.amount == 12345
    assert pending.add_pending.merchant == "Test Merchant"
    assert pending.add_pending.category == "Test Category"
    assert pending.add_pending.description == "Test Desc"
    assert isinstance(cleared, BankEvent)
    assert cleared.add_cleared is not None
    assert isinstance(cleared.add_cleared, AddCleared)
    assert cleared.add_cleared.amount == 12345
    assert cleared.add_cleared.merchant == "Test Merchant"
    assert cleared.add_cleared.category == "Test Category"
    assert cleared.add_cleared.description == "Test Desc"
    assert isinstance(remove_pending, BankEvent)
    assert remove_pending.remove_pending is not None
    assert isinstance(remove_pending.remove_pending, RemovePending)
    assert remove_pending.remove_pending.reason == "cleared"
    # Timestamps should be microsecond-precision ISO8601
    assert pending.timestamp.endswith("Z")
    assert len(pending.timestamp.split(".")[-1]) == 7  # .123456Z
    assert cleared.timestamp.endswith("Z")
    assert len(cleared.timestamp.split(".")[-1]) == 7
    assert remove_pending.timestamp.endswith("Z")
    assert len(remove_pending.timestamp.split(".")[-1]) == 7
