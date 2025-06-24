"""
Unit tests for bedrock serialization/deserialization.
"""

# Standard library
import tempfile
from pathlib import Path

# Third-party
import pytest

# Local project
from doppelbank.bedrock.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
)
from doppelbank.bedrock.serde import (
    load_events,
    load_events_binary,
    load_events_csv,
    load_events_json,
    save_events,
    save_events_binary,
    save_events_csv,
    save_events_json,
)


class TestJsonSerde:
    """Test JSON serialization/deserialization."""

    def test_save_load_events_json(self):
        """Test saving and loading events in JSON format."""
        events = [
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
            save_events_json(events, file_path)
            loaded_events = load_events_json(file_path)

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


class TestCsvSerde:
    """Test CSV serialization/deserialization."""

    def test_save_load_events_csv(self):
        """Test saving and loading events in CSV format."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
            create_transfer_event(
                "42", 10000, "2025-01-01T12:00:00Z", "checking", "savings"
            ),
            create_card_swipe_event(
                "42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink"
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events_csv(events, file_path)
            loaded_events = load_events_csv(file_path)

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

    def test_save_events_csv_empty(self):
        """Test saving empty events list to CSV."""
        events = []

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events_csv(events, file_path)
            # Should not raise an exception
            assert file_path.exists()
        finally:
            file_path.unlink()


class TestBinarySerde:
    """Test binary protobuf serialization/deserialization."""

    def test_save_load_events_binary(self):
        """Test saving and loading events in binary format."""
        events = [
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
            save_events_binary(events, file_path)
            loaded_events = load_events_binary(file_path)

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


class TestFormatDetection:
    """Test automatic format detection."""

    def test_load_events_json_extension(self):
        """Test loading events with .json extension."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events_json(events, file_path)
            loaded_events = load_events(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_load_events_csv_extension(self):
        """Test loading events with .csv extension."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events_csv(events, file_path)
            loaded_events = load_events(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_load_events_binary_extension(self):
        """Test loading events with .bin extension."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events_binary(events, file_path)
            loaded_events = load_events(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_load_events_unsupported_extension(self):
        """Test loading events with unsupported extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            file_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                load_events(file_path)
        finally:
            file_path.unlink()


class TestSaveEvents:
    """Test the main save_events function."""

    def test_save_events_json_format(self):
        """Test save_events with JSON format."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events(events, file_path, "json")
            loaded_events = load_events_json(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_save_events_csv_format(self):
        """Test save_events with CSV format."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events(events, file_path, "csv")
            loaded_events = load_events_csv(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_save_events_binary_format(self):
        """Test save_events with binary format."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            file_path = Path(f.name)

        try:
            save_events(events, file_path, "binary")
            loaded_events = load_events_binary(file_path)

            assert len(loaded_events) == 1
            assert loaded_events[0].paycheck.user_id == "42"

        finally:
            file_path.unlink()

    def test_save_events_unsupported_format(self):
        """Test save_events with unsupported format."""
        events = [
            create_paycheck_event("42", 250000, "2025-01-01T12:00:00Z", "Acme Corp"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            file_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported format"):
                save_events(events, file_path, "unsupported")
        finally:
            file_path.unlink()
