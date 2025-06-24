from generated.bedrock import EventCollection, Event, PaycheckEvent
from doppelbank.detritus.cli import bedrock_to_detritus

def test_bedrock_to_detritus_minimal():
    event = Event(paycheck=PaycheckEvent(user_id="u1", amount=100, timestamp="2024-01-01T00:00:00Z", employer="Acme", description="desc"))
    collection = EventCollection(events=[event])
    sync = bedrock_to_detritus(collection)
    assert hasattr(sync, "added")
    assert isinstance(sync.added, list)
    assert len(sync.added) == 1
    t = sync.added[0]
    assert t.transaction_id == "u1"
    assert t.account_id == "acc_dummy" 