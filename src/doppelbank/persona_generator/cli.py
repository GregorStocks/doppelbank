#!/usr/bin/env python3
"""
Persona Generator CLI - Combines Bedrock (event generation) and Detritus (event transformation).

Generates structured, human-readable events and transforms them into Plaid-style sync data.
"""

# Standard library
import argparse
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Third-party
import pytz

from doppelbank.lib.ids import AccountId, ItemId, UserId
from doppelbank.lib.logging_config import configure_logging
from doppelbank.lib.serde import save_binary, save_json

# Local project
from doppelbank.persona_generator.models import (
    create_card_swipe_event,
    create_paycheck_event,
)
from doppelbank.persona_generator.transform import bedrock_to_detritus
from doppelbank.schemas.bedrock import EventCollection


class PersonaInfo:
    """Persona information for generating personalized financial events."""

    def __init__(
        self,
        persona_name: str,
        timezone_name: str = "US/Pacific",
        employer: str = "Acme Corp",
        salary: float = 65000.0,
        spending_patterns: dict[str, Any] | None = None,
    ):
        self.persona_name = persona_name
        self.timezone_name = timezone_name
        self.employer = employer
        self.salary = salary
        self.spending_patterns = spending_patterns or {}

    def get_timezone(self) -> pytz.BaseTzInfo:
        """Get the timezone object for this persona."""
        return pytz.timezone(self.timezone_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert persona info to dictionary."""
        return {
            "persona_name": self.persona_name,
            "timezone_name": self.timezone_name,
            "employer": self.employer,
            "salary": self.salary,
            "spending_patterns": self.spending_patterns,
        }


def generate_random_timestamp(base_date: datetime, persona_info: PersonaInfo) -> datetime:
    """Generate a random timestamp within the given date."""
    # Generate random time components
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 999999)

    persona_tz = persona_info.get_timezone()
    local_time = base_date.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)

    return persona_tz.localize(local_time)


def generate_events(
    persona_info: PersonaInfo,
    account_id: str,
    days: int = 30,
    seed: int | None = None,
) -> EventCollection:
    """Generate a sequence of financial events for a persona. All amounts are int cents."""
    events_list = []

    # Set seed for deterministic generation
    if seed is not None:
        random.seed(seed)

    # Generate events for the specified number of days
    start_date = datetime.now() - timedelta(days=days)

    # Calculate bi-weekly paycheck amount (int cents)
    biweekly_pay = int(round(persona_info.salary * 100 / 26))  # 26 pay periods per year

    current_date = start_date
    while current_date <= datetime.now():
        # Generate paycheck every 2 weeks
        if current_date.weekday() == 4 and current_date.day % 14 < 7:  # Every other Friday
            timestamp = generate_random_timestamp(current_date, persona_info)
            events_list.append(
                create_paycheck_event(
                    account_id=account_id,
                    amount=biweekly_pay,
                    timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    employer=persona_info.employer,
                    description="Bi-weekly paycheck",
                )
            )

        # Generate some random card swipes
        if current_date.weekday() < 5:  # Weekdays
            merchants = ["Starbucks", "Subway", "CVS", "Target", "Amazon"]
            categories = ["Food & Drink", "Shopping", "Transportation", "Entertainment"]

            for _ in range(2):  # 2 purchases per weekday
                merchant = random.choice(merchants)
                category = random.choice(categories)
                amount = int(round(random.uniform(5.0, 50.0) * 100))  # int cents
                timestamp = generate_random_timestamp(current_date, persona_info)
                events_list.append(
                    create_card_swipe_event(
                        account_id=account_id,
                        amount=-amount,  # Negative for spending
                        timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        merchant=merchant,
                        category=category,
                        description=f"Purchase at {merchant}",
                    )
                )

        current_date += timedelta(days=1)

    return EventCollection(events=events_list)


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.days <= 0:
        raise ValueError("Days must be positive")

    if args.format not in ["json", "binary"]:
        raise ValueError("Output format must be 'json' or 'binary'")

    # Validate hierarchical ID components
    if not args.user_id:
        raise ValueError("User ID cannot be empty")
    if not args.persona:
        raise ValueError("Persona name cannot be empty")
    if not args.institution:
        raise ValueError("Institution ID cannot be empty")
    if not args.account_type:
        raise ValueError("Account type cannot be empty")


def main() -> None:
    """Main CLI entry point."""
    # Configure logging to show INFO level messages by default
    configure_logging(module_name="persona_generator")

    logger = logging.getLogger(__name__)
    logger.info("Starting Persona Generator CLI")

    parser = argparse.ArgumentParser(
        description="Persona Generator - Generate and transform financial events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user-id user_123 --persona jimmy --institution doppelbank \\
      --account-type checking --days 30
  %(prog)s --user-id client_user --persona claude --institution doppelfirstbank \\
      --account-type savings --days 60 --seed 12345
        """,
    )

    # Main command - create complete persona data (generate + transform in one step)
    parser.add_argument("--user-id", required=True, help="User ID for hierarchical structure")
    parser.add_argument("--persona", required=True, help="Persona name (e.g., jimmy, claude)")
    parser.add_argument("--institution", required=True, help="Institution ID (e.g., doppelbank)")
    parser.add_argument(
        "--account-type", required=True, help="Account type (e.g., checking, savings)"
    )
    parser.add_argument(
        "--timezone", default="US/Pacific", help="User timezone (default: US/Pacific)"
    )
    parser.add_argument(
        "--employer", default="Acme Corp", help="Employer name (default: Acme Corp)"
    )
    parser.add_argument(
        "--salary", type=float, default=65000.0, help="Annual salary (default: 65000)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to generate (default: 30)",
    )
    parser.add_argument("--seed", type=int, help="Random seed for deterministic generation")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output detritus ledger file (optional, defaults to data/ structure)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "binary"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    try:
        validate_args(args)

        # Create hierarchical IDs
        user_id = UserId(args.user_id)
        item_id = ItemId(args.user_id, args.persona, args.institution)
        account_id = AccountId(args.user_id, args.persona, args.institution, args.account_type)

        logger.info(f"Creating persona data for {item_id.to_wire()}")
        logger.info(f"Account: {account_id.to_wire()}")

        # Create persona info object
        persona_info = PersonaInfo(
            persona_name=args.persona,
            timezone_name=args.timezone,
            employer=args.employer,
            salary=args.salary,
        )

        print(f"Generating {args.days} days of events for persona {args.persona}...")
        print(f"  User ID: {user_id.to_wire()}")
        print(f"  Item ID: {item_id.to_wire()}")
        print(f"  Account ID: {account_id.to_wire()}")
        print(f"  Institution: {args.institution}")
        print(f"  Timezone: {args.timezone}")
        print(f"  Employer: {args.employer}")
        print(f"  Annual Salary: ${args.salary:,.2f}")

        # Generate events
        events = generate_events(
            persona_info=persona_info,
            account_id=account_id.to_wire(),
            days=args.days,
            seed=args.seed,
        )

        logger.info(f"Generated {len(events.events)} events")

        # Transform to detritus ledger
        detritus_ledger = bedrock_to_detritus(events)

        # Create directory structure and save files
        if args.output:
            # Use specified output file
            if args.format == "json":
                save_json(detritus_ledger, args.output)
            else:
                save_binary(detritus_ledger, args.output)
            logger.info(f"Saved detritus ledger to {args.output}")
            print(f"Saved ledger to {args.output}")
        else:
            # Use hierarchical data structure
            data_root = Path("data")
            persona_dir = data_root / "personas" / args.persona
            institution_dir = persona_dir / args.institution

            # Create directories
            institution_dir.mkdir(parents=True, exist_ok=True)

            # Save persona metadata
            persona_file = persona_dir / "persona.json"
            if not persona_file.exists():
                persona_metadata = persona_info.to_dict()
                with open(persona_file, "w") as f:
                    json.dump(persona_metadata, f, indent=2)
                logger.info(f"Created persona metadata: {persona_file}")

            # Save account ledger
            account_file = institution_dir / f"{args.account_type}.json"
            if args.format == "json":
                save_json(detritus_ledger, account_file)
            else:
                save_binary(detritus_ledger, account_file)

            logger.info(f"Saved account ledger to {account_file}")
            print(
                f"Generated {len(events.events)} events and saved to hierarchical data structure:"
            )
            print(f"  Persona: {persona_file}")
            print(f"  Account: {account_file}")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
