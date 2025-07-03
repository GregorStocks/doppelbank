"""
Unit tests for bedrock models.
"""

# Standard library

# Third-party
# Local project
from doppelbank.persona_generator.models import (
    create_card_swipe_event,
    create_paycheck_event,
    get_event_summary,
)
from doppelbank.schemas.bedrock import (
    CardSwipeEvent,
    PaycheckEvent,
)


class TestEventCreation:
    """Test event creation functions."""

    def test_create_paycheck_event(self) -> None:
        """Test paycheck event creation."""
        event = create_paycheck_event(
            amount=250000,  # $2500.00 in cents
            timestamp="2025-01-01T12:00:00Z",
            employer="Acme Corp",
            description="Test paycheck",
        )

        assert isinstance(event, PaycheckEvent)
        assert event.amount == 250000
        assert event.timestamp == "2025-01-01T12:00:00Z"
        assert event.employer == "Acme Corp"
        assert event.description == "Test paycheck"

    def test_create_card_swipe_event(self) -> None:
        """Test card swipe event creation."""
        event = create_card_swipe_event(
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
            description="Test purchase",
        )

        assert isinstance(event, CardSwipeEvent)
        assert event.amount == -2550
        assert event.timestamp == "2025-01-01T12:00:00Z"
        assert event.merchant == "Starbucks"
        assert event.category == "Food & Drink"
        assert event.description == "Test purchase"

    def test_create_card_swipe_event_default_description(self) -> None:
        """Test card swipe event creation with default description."""
        event = create_card_swipe_event(
            amount=-2550,  # -$25.50 in cents
            timestamp="2025-01-01T12:00:00Z",
            merchant="Starbucks",
            category="Food & Drink",
        )

        assert isinstance(event, CardSwipeEvent)
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
                250000,
                "2025-01-01T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
            create_card_swipe_event(
                -2550,
                "2025-01-01T12:00:00Z",
                "Starbucks",
                "Food & Drink",
                "Purchase at Starbucks",
            ),
            create_paycheck_event(
                250000,
                "2025-01-02T12:00:00Z",
                "Acme Corp",
                "Bi-weekly paycheck",
            ),
        ]

        summary = get_event_summary(events)

        assert summary["paycheck"] == 2
        assert summary["card_swipe"] == 1
        assert summary["total"] == 3
