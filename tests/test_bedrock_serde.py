"""
Unit tests for bedrock serialization/deserialization.
"""

# Standard library
import tempfile
from pathlib import Path

from doppelbank.lib.serde import load_binary, load_json, save_binary, save_json

# Third-party
# Local project
from doppelbank.persona_generator.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
)
from doppelbank.schemas.bedrock import (
    CardSwipeEvent,
    EventCollection,
    PaycheckEvent,
    TransferEvent,
)


class TestJsonSerde:
    """Test JSON serialization/deserialization."""

    def test_save_load_events_json(self) -> None:
        """Test saving and loading events in JSON format."""
        event_collection = EventCollection(
            events=[
                create_paycheck_event(
                    "acc_42",
                    250000,
                    "2025-01-01T12:00:00Z",
                    "Acme Corp",
                    "Bi-weekly paycheck",
                ),
                create_transfer_event(
                    10000, "2025-01-01T12:00:00Z", "checking", "savings"
                ),
                create_card_swipe_event(
                    "acc_42",
                    -2550,
                    "2025-01-01T12:00:00Z",
                    "Starbucks",
                    "Food & Drink",
                    "Purchase at Starbucks",
                ),
            ]
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_json(event_collection, file_path)
            loaded_events = load_json(file_path, EventCollection).events

            assert len(loaded_events) == 3

            # Check paycheck event
            assert isinstance(loaded_events[0], PaycheckEvent)
            assert loaded_events[0].user_id == ""
            assert loaded_events[0].amount == 250000
            assert loaded_events[0].employer == "Acme Corp"

            # Check transfer event
            assert isinstance(loaded_events[1], TransferEvent)
            assert loaded_events[1].user_id == ""
            assert loaded_events[1].amount == 10000
            assert loaded_events[1].from_account == "checking"
            assert loaded_events[1].to_account == "savings"

            # Check card swipe event
            assert isinstance(loaded_events[2], CardSwipeEvent)
            assert loaded_events[2].user_id == ""
            assert loaded_events[2].amount == -2550
            assert loaded_events[2].merchant == "Starbucks"
            assert loaded_events[2].category == "Food & Drink"

        finally:
            file_path.unlink()


class TestBinarySerde:
    """Test binary protobuf serialization/deserialization."""

    def test_save_load_events_binary(self) -> None:
        """Test saving and loading events in binary format."""
        event_collection = EventCollection(
            events=[
                create_paycheck_event(
                    "acc_42",
                    250000,
                    "2025-01-01T12:00:00Z",
                    "Acme Corp",
                    "Bi-weekly paycheck",
                ),
                create_transfer_event(
                    10000, "2025-01-01T12:00:00Z", "checking", "savings"
                ),
                create_card_swipe_event(
                    "acc_42",
                    -2550,
                    "2025-01-01T12:00:00Z",
                    "Starbucks",
                    "Food & Drink",
                    "Purchase at Starbucks",
                ),
            ]
        )

        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_binary(event_collection, file_path)
            loaded_events = load_binary(file_path, EventCollection).events

            assert len(loaded_events) == 3

            # Check paycheck event
            assert isinstance(loaded_events[0], PaycheckEvent)
            assert loaded_events[0].user_id == ""
            assert loaded_events[0].amount == 250000
            assert loaded_events[0].employer == "Acme Corp"

            # Check transfer event
            assert isinstance(loaded_events[1], TransferEvent)
            assert loaded_events[1].user_id == ""
            assert loaded_events[1].amount == 10000
            assert loaded_events[1].from_account == "checking"
            assert loaded_events[1].to_account == "savings"

            # Check card swipe event
            assert isinstance(loaded_events[2], CardSwipeEvent)
            assert loaded_events[2].user_id == ""
            assert loaded_events[2].amount == -2550
            assert loaded_events[2].merchant == "Starbucks"
            assert loaded_events[2].category == "Food & Drink"

        finally:
            file_path.unlink()
