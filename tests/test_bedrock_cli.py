"""
Unit tests for bedrock CLI.
"""

# Standard library

# Third-party

# Local project
from doppelbank.bedrock.cli import UserInfo, generate_events, generate_random_timestamp


class TestUserInfo:
    """Test UserInfo class."""

    def test_to_dict(self):
        """Test to_dict method."""
        user_info = UserInfo(
            user_id="42",
            timezone_name="US/Pacific",
            employer="Acme Corp",
            salary=65000.0,
            spending_patterns={"food": 0.3},
        )

        result = user_info.to_dict()

        assert result == {
            "user_id": "42",
            "timezone_name": "US/Pacific",
            "employer": "Acme Corp",
            "salary": 65000.0,
            "spending_patterns": {"food": 0.3},
        }


class TestGenerateRandomTimestamp:
    """Test timestamp generation."""

    def test_generate_random_timestamp(self):
        """Test random timestamp generation."""
        from datetime import datetime

        user_info = UserInfo("42", timezone_name="US/Pacific")
        base_date = datetime(2025, 1, 1)

        timestamp = generate_random_timestamp(base_date, user_info)

        assert timestamp.year == 2025
        assert timestamp.month == 1
        assert timestamp.day == 1
        assert 0 <= timestamp.hour <= 23
        assert 0 <= timestamp.minute <= 59
        assert 0 <= timestamp.second <= 59
        assert timestamp.tzinfo is not None


class TestGenerateEvents:
    """Test event generation."""

    def test_generate_events_with_seed(self):
        """Test event generation with seed for deterministic output."""
        user_info = UserInfo("42")

        events = generate_events(user_info, months=1, seed=42)

        assert len(events.events) > 0

        # With the same seed, we should get the same events
        events2 = generate_events(user_info, months=1, seed=42)

        assert len(events.events) == len(events2.events)

        # Check that the events are identical
        for i in range(len(events.events)):
            assert events.events[i].to_dict() == events2.events[i].to_dict()

    def test_generate_events_no_seed(self):
        """Test event generation without seed."""
        user_info = UserInfo("42")

        events = generate_events(user_info, months=1)

        assert len(events.events) > 0

    def test_generate_events_paycheck_amount(self):
        """Test that paycheck amounts are calculated correctly."""
        user_info = UserInfo("42", salary=52000.0)  # $52k/year

        events = generate_events(user_info, months=1, seed=42)

        # Find paycheck events
        paycheck_events = [e for e in events.events if e.paycheck.user_id]

        assert len(paycheck_events) > 0

        # Bi-weekly pay should be 52000 / 26 = 2000 dollars, or 200000 cents
        expected_pay = int(round(52000.0 * 100 / 26))

        for event in paycheck_events:
            assert event.paycheck.amount == expected_pay
            assert event.paycheck.employer == "Acme Corp"

    def test_generate_events_card_swipe_negative_amounts(self):
        """Test that card swipe events have negative amounts."""
        user_info = UserInfo("42")

        events = generate_events(user_info, months=1, seed=42)

        # Find card swipe events
        card_swipe_events = [e for e in events.events if e.card_swipe.user_id]

        assert len(card_swipe_events) > 0

        for event in card_swipe_events:
            assert event.card_swipe.amount < 0  # Should be negative for spending
            assert event.card_swipe.merchant in [
                "Starbucks",
                "Subway",
                "CVS",
                "Target",
                "Amazon",
            ]
            assert event.card_swipe.category in [
                "Food & Drink",
                "Shopping",
                "Transportation",
                "Entertainment",
            ]

    def test_generate_events_timestamps(self):
        """Test that events have proper timestamps."""
        user_info = UserInfo("42")

        events = generate_events(user_info, months=1, seed=42)

        assert len(events.events) > 0

        for event in events.events:
            # Check that timestamp is in the expected format
            if event.paycheck.user_id:
                timestamp = event.paycheck.timestamp
            elif event.transfer.user_id:
                timestamp = event.transfer.timestamp
            elif event.card_swipe.user_id:
                timestamp = event.card_swipe.timestamp
            else:
                continue

            # Should end with Z (UTC)
            assert timestamp.endswith("Z")

            # Should be parseable as datetime
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            assert dt.year >= 2024  # Should be recent
