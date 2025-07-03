"""
Unit tests for bedrock CLI.
"""

# Standard library

# Third-party
# Local project
from doppelbank.persona_generator.cli import (
    PersonaInfo,
    generate_events,
)
from doppelbank.schemas.bedrock import PaycheckEvent


class TestGenerateEvents:
    """Test event generation."""

    def test_generate_events_paycheck_amount(self) -> None:
        """Test that paycheck amounts are calculated correctly."""
        persona_info = PersonaInfo("test_persona", salary=52000.0)  # $52k/year

        events = generate_events(
            persona_info,
            days=30,
        )

        # Find paycheck events
        paycheck_events = [e for e in events.events if isinstance(e, PaycheckEvent)]

        assert len(paycheck_events) > 0

        # Bi-weekly pay should be 52000 / 26 = 2000 dollars, or 200000 cents
        expected_pay = int(round(52000.0 * 100 / 26))

        for event in paycheck_events:
            assert isinstance(event, PaycheckEvent)
            assert event.amount == expected_pay
            assert event.employer == "Acme Corp"
