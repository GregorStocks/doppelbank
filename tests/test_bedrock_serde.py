"""
Unit tests for bedrock serialization/deserialization.
"""

# Standard library
import tempfile
from pathlib import Path

# Third-party
# Local project
from doppelbank.bedrock.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
)
from doppelbank.lib.serde import load_binary, load_json, save_binary, save_json
from generated.bedrock import EventCollection


class TestJsonSerde:
    """Test JSON serialization/deserialization."""

    def test_save_load_events_json(self) -> None:
        """Test saving and loading events in JSON format."""
        event_collection = EventCollection()
        event_collection.events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
            create_transfer_event(
                "42", 10000, "2025-01-01T12:00:00Z", "checking", "savings"
            ),
            create_card_swipe_event(
                "42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink"
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_json(event_collection, file_path)
            loaded_events = load_json(file_path, EventCollection).events

            assert len(loaded_events) == 3

            # Check paycheck event
            assert loaded_events[0].paycheck.user_id == "42"
            assert loaded_events[0].paycheck.amount == 250000
            assert loaded_events[0].paycheck.employer == "Acme Corp"

            # Check transfer event
            assert loaded_events[1].transfer.user_id == "42"
            assert loaded_events[1].transfer.amount == 10000
            assert loaded_events[1].transfer.from_account == "checking"
            assert loaded_events[1].transfer.to_account == "savings"

            # Check card swipe event
            assert loaded_events[2].card_swipe.user_id == "42"
            assert loaded_events[2].card_swipe.amount == -2550
            assert loaded_events[2].card_swipe.merchant == "Starbucks"
            assert loaded_events[2].card_swipe.category == "Food & Drink"

        finally:
            file_path.unlink()


class TestBinarySerde:
    """Test binary protobuf serialization/deserialization."""

    def test_save_load_events_binary(self) -> None:
        """Test saving and loading events in binary format."""
        event_collection = EventCollection()
        event_collection.events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
            create_transfer_event(
                "42", 10000, "2025-01-01T12:00:00Z", "checking", "savings"
            ),
            create_card_swipe_event(
                "42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink"
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_binary(event_collection, file_path)
            loaded_events = load_binary(file_path, EventCollection).events

            assert len(loaded_events) == 3

            # Check paycheck event
            assert loaded_events[0].paycheck.user_id == "42"
            assert loaded_events[0].paycheck.amount == 250000
            assert loaded_events[0].paycheck.employer == "Acme Corp"

            # Check transfer event
            assert loaded_events[1].transfer.user_id == "42"
            assert loaded_events[1].transfer.amount == 10000
            assert loaded_events[1].transfer.from_account == "checking"
            assert loaded_events[1].transfer.to_account == "savings"

            # Check card swipe event
            assert loaded_events[2].card_swipe.user_id == "42"
            assert loaded_events[2].card_swipe.amount == -2550
            assert loaded_events[2].card_swipe.merchant == "Starbucks"
            assert loaded_events[2].card_swipe.category == "Food & Drink"

        finally:
            file_path.unlink()
