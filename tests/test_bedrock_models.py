"""
Unit tests for bedrock models.
"""

# Standard library

# Third-party
# Local project
from doppelbank.persona_generator.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
    get_event_summary,
)
from doppelbank.schemas.bedrock import (
    CardSwipeEvent,
    PaycheckEvent,
    TransferEvent,
)


class TestEventCreation:
    """Test event creation functions."""

    def test_create_paycheck_event(self) -> None:
        """Test paycheck event creation."""
        event = create_paycheck_event(
            account_id="acc_42",
            amount=250000,  # $2500.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            employer="Acme Corp",
            description="Test paycheck",
        )

        assert isinstance(event, PaycheckEvent)
        assert event.user_id == ""
        assert event.amount == 250000
        assert event.timestamp == "2025-01-01T12:00:00Z"
        assert event.employer == "Acme Corp"
        assert event.description == "Test paycheck"

    def test_create_transfer_event(self) -> None:
        """Test transfer event creation."""
        event = create_transfer_event(
            amount=10000,  # $100.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            from_account="checking",
            to_account="savings",
            description="Test transfer",
        )

        assert isinstance(event, TransferEvent)
        assert event.user_id == ""
        assert event.amount == 10000
        assert event.timestamp == "2025-01-01T12:00:00Z"
        assert event.from_account == "checking"
        assert event.to_account == "savings"
        assert event.description == "Test transfer"

    def test_create_transfer_event_default_description(self) -> None:
        """Test transfer event creation with default description."""
        event = create_transfer_event(
            amount=10000,  # $100.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            from_account="checking",
            to_account="savings",
        )

        assert isinstance(event, TransferEvent)
        assert event.user_id == ""
        assert event.description == "Transfer from checking to savings"

    def test_create_card_swipe_event(self) -> None:
        """Test card swipe event creation."""
        event = create_card_swipe_event(
            account_id="acc_42",
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
            description="Test purchase",
        )

        assert isinstance(event, CardSwipeEvent)
        assert event.user_id == ""
        assert event.amount == -2550
        assert event.timestamp == "2025-01-01T12:00:00Z"
        assert event.merchant == "Starbucks"
        assert event.category == "Food & Drink"
        assert event.description == "Test purchase"

    def test_create_card_swipe_event_default_description(self) -> None:
        """Test card swipe event creation with default description."""
        event = create_card_swipe_event(
            account_id="acc_42",
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
        )

        assert isinstance(event, CardSwipeEvent)
        assert event.user_id == ""
        assert event.description == "Purchase at Starbucks"


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
            create_paycheck_event(
                "acc_42",
                250000,
                "2025-01-01T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
            create_transfer_event(10000, "2025-01-01T12:00:00Z", "checking", "savings"),
            create_card_swipe_event(
                "acc_42",
                -2550,
                "2025-01-01T12:00:00Z",
                "Starbucks",
                "Food & Drink",
                "Purchase at Starbucks",
            ),
            create_paycheck_event(
                "acc_42",
                250000,
                "2025-01-02T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
        ]

        summary = get_event_summary(events)

        assert summary["paycheck"] == 2
        assert summary["transfer"] == 1
        assert summary["card_swipe"] == 1
        assert summary["total"] == 4

    def test_get_event_summary_only_paychecks(self) -> None:
        """Test event summary with only paycheck events."""
        events = [
            create_paycheck_event(
                "acc_42",
                250000,
                "2025-01-01T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
            create_paycheck_event(
                "acc_42",
                250000,
                "2025-01-02T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
        ]

        summary = get_event_summary(events)

        assert summary["paycheck"] == 2
        assert summary["transfer"] == 0
        assert summary["card_swipe"] == 0
        assert summary["total"] == 2


class TestEventTypeBehavior:
    """Test event type detection behavior."""

    def test_event_type_detection_with_paycheck(self) -> None:
        """Test event type detection with paycheck event."""
        event = create_paycheck_event(
            "acc_42",
            250000,
            "2025-01-01T12:00:00Z",
            "Acme Corp",
            "Bi-weekly paycheck",
        )

        assert isinstance(event, PaycheckEvent)
        assert event.user_id == ""

    def test_event_type_detection_with_transfer(self) -> None:
        """Test event type detection with transfer event."""
        event = create_transfer_event(10000, "2025-01-01T12:00:00Z", "checking", "savings")

        assert isinstance(event, TransferEvent)
        assert event.user_id == ""

    def test_event_type_detection_with_card_swipe(self) -> None:
        """Test event type detection with card swipe event."""
        event = create_card_swipe_event(
            "acc_42",
            -2550,
            "2025-01-01T12:00:00Z",
            "Starbucks",
            "Food & Drink",
            "Purchase at Starbucks",
        )

        assert isinstance(event, CardSwipeEvent)
        assert event.user_id == ""

    def test_event_union_structure(self) -> None:
        """Test that Event is a proper union type."""
        # Event is now a union type, so we can't create empty instances
        # Instead, test that our create functions return the right types
        paycheck = create_paycheck_event("acc_42", 250000, "2025-01-01T12:00:00Z", "Acme Corp")
        transfer = create_transfer_event(10000, "2025-01-01T12:00:00Z", "checking", "savings")
        card_swipe = create_card_swipe_event(
            "acc_42", -2550, "2025-01-01T12:00:00Z", "Starbucks", "Food & Drink"
        )

        assert isinstance(paycheck, PaycheckEvent)
        assert isinstance(transfer, TransferEvent)
        assert isinstance(card_swipe, CardSwipeEvent)
