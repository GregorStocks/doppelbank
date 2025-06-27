"""
Unit tests for bedrock models.
"""

# Standard library

# Third-party
import betterproto

# Local project
from doppelbank.bedrock.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
    get_event_summary,
)
from generated.bedrock import Event


class TestEventCreation:
    """Test event creation functions."""

    def test_create_paycheck_event(self) -> None:
        """Test paycheck event creation."""
        event = create_paycheck_event(
            user_id="42",
            account_id="acc_42",
            amount=250000,  # $2500.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            employer="Acme Corp",
            description="Test paycheck",
        )

        assert event.paycheck is not None
        assert event.paycheck.user_id == "42"
        assert event.paycheck.amount == 250000
        assert event.paycheck.timestamp == "2025-01-01T12:00:00Z"
        assert event.paycheck.employer == "Acme Corp"
        assert event.paycheck.description == "Test paycheck"

        # Check that other fields are empty
        assert event.transfer is not None
        assert event.transfer.user_id == ""
        assert event.card_swipe is not None
        assert event.card_swipe.user_id == ""

    def test_create_transfer_event(self) -> None:
        """Test transfer event creation."""
        event = create_transfer_event(
            user_id="42",
            amount=10000,  # $100.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            from_account="checking",
            to_account="savings",
            description="Test transfer",
        )

        assert event.transfer is not None
        assert event.transfer.user_id == "42"
        assert event.transfer.amount == 10000
        assert event.transfer.timestamp == "2025-01-01T12:00:00Z"
        assert event.transfer.from_account == "checking"
        assert event.transfer.to_account == "savings"
        assert event.transfer.description == "Test transfer"

        # Check that other fields are empty
        assert event.paycheck is not None
        assert event.paycheck.user_id == ""
        assert event.card_swipe is not None
        assert event.card_swipe.user_id == ""

    def test_create_transfer_event_default_description(self) -> None:
        """Test transfer event creation with default description."""
        event = create_transfer_event(
            user_id="42",
            amount=10000,  # $100.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            from_account="checking",
            to_account="savings",
        )

        assert event.transfer.description == "Transfer from checking to savings"

    def test_create_card_swipe_event(self) -> None:
        """Test card swipe event creation."""
        event = create_card_swipe_event(
            user_id="42",
            account_id="acc_42",
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
            description="Test purchase",
        )

        assert event.card_swipe is not None
        assert event.card_swipe.user_id == "42"
        assert event.card_swipe.amount == -2550
        assert event.card_swipe.timestamp == "2025-01-01T12:00:00Z"
        assert event.card_swipe.merchant == "Starbucks"
        assert event.card_swipe.category == "Food & Drink"
        assert event.card_swipe.description == "Test purchase"

        # Check that other fields are empty
        assert event.paycheck is not None
        assert event.paycheck.user_id == ""
        assert event.transfer is not None
        assert event.transfer.user_id == ""

    def test_create_card_swipe_event_default_description(self) -> None:
        """Test card swipe event creation with default description."""
        event = create_card_swipe_event(
            user_id="42",
            account_id="acc_42",
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
        )

        assert event.card_swipe.description == "Purchase at Starbucks"


class TestEventSummary:
    """Test event summary functionality."""

    def test_get_event_summary_empty(self) -> None:
        """Test event summary with empty list."""
        summary = get_event_summary([])

        assert summary["paycheck"] == 0
        assert summary["transfer"] == 0
        assert summary["card_swipe"] == 0
        assert summary["total"] == 0

    def test_get_event_summary_mixed_events(self) -> None:
        """Test event summary with mixed event types."""
        events = [
            create_paycheck_event("42", "acc_42", 250000, "2025-01-01T12:00:00Z", "Acme Corp", "Bi-weekly paycheck"),
            create_transfer_event(
                "42", 10000, "2025-01-01T12:00:00Z", "checking", "savings"
            ),
            create_card_swipe_event(
                "42", "acc_42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink", "Purchase at Starbucks"
            ),
            create_paycheck_event("42", "acc_42", 250000, "2025-01-02T12:00:00Z", "Acme Corp", "Bi-weekly paycheck"),
        ]

        summary = get_event_summary(events)

        assert summary["paycheck"] == 2
        assert summary["transfer"] == 1
        assert summary["card_swipe"] == 1
        assert summary["total"] == 4

    def test_get_event_summary_only_paychecks(self) -> None:
        """Test event summary with only paycheck events."""
        events = [
            create_paycheck_event("42", "acc_42", 250000, "2025-01-01T12:00:00Z", "Acme Corp", "Bi-weekly paycheck"),
            create_paycheck_event("42", "acc_42", 250000, "2025-01-02T12:00:00Z", "Acme Corp", "Bi-weekly paycheck"),
        ]

        summary = get_event_summary(events)

        assert summary["paycheck"] == 2
        assert summary["transfer"] == 0
        assert summary["card_swipe"] == 0
        assert summary["total"] == 2


class TestOneOfBehavior:
    """Test oneof field behavior."""

    def test_which_one_of_with_paycheck(self) -> None:
        """Test which_one_of with paycheck event."""
        event = create_paycheck_event("42", "acc_42", 250000, "2025-01-01T12:00:00Z", "Acme Corp", "Bi-weekly paycheck")
        field_name, value = betterproto.which_one_of(event, "event_data")

        assert field_name == "paycheck"
        assert value is not None
        assert value.user_id == "42"

    def test_which_one_of_with_transfer(self) -> None:
        """Test which_one_of with transfer event."""
        event = create_transfer_event(
            "42", 10000, "2025-01-01T12:00:00Z", "checking", "savings"
        )
        field_name, value = betterproto.which_one_of(event, "event_data")

        assert field_name == "transfer"
        assert value is not None
        assert value.user_id == "42"

    def test_which_one_of_with_card_swipe(self) -> None:
        """Test which_one_of with card swipe event."""
        event = create_card_swipe_event(
            "42", "acc_42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink", "Purchase at Starbucks"
        )
        field_name, value = betterproto.which_one_of(event, "event_data")

        assert field_name == "card_swipe"
        assert value is not None
        assert value.user_id == "42"

    def test_which_one_of_empty_event(self) -> None:
        """Test which_one_of with empty event."""
        event = Event()
        field_name, value = betterproto.which_one_of(event, "event_data")

        assert field_name == ""
        assert value is None
