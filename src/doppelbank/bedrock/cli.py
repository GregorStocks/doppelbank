#!/usr/bin/env python3
"""
Bedrock CLI - Simulates the "real world" financial events.

Generates structured, human-readable events such as paychecks, transfers,
card-swipes, etc. that represent real-world financial activities.
"""

# Standard library
import argparse
import logging
import random
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Third-party
import pytz

# Local project
from doppelbank.bedrock.models import (
    create_card_swipe_event,
    create_paycheck_event,
    get_event_summary,
)
from doppelbank.lib.logging_config import configure_logging
from doppelbank.lib.serde import load_binary, load_json, save_binary, save_json
from generated.bedrock import EventCollection


class UserInfo:
    """User information for generating personalized financial events."""

    def __init__(
        self,
        user_id: str,
        account_id: str,
        timezone_name: str = "US/Pacific",
        employer: str = "Acme Corp",
        salary: float = 65000.0,
        spending_patterns: dict[str, Any] | None = None,
    ):
        self.user_id = user_id
        self.account_id = account_id
        self.timezone_name = timezone_name
        self.employer = employer
        self.salary = salary
        self.spending_patterns = spending_patterns or {}

    def get_timezone(self) -> pytz.BaseTzInfo:
        """Get the timezone object for this user."""
        return pytz.timezone(self.timezone_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert user info to dictionary."""
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "timezone_name": self.timezone_name,
            "employer": self.employer,
            "salary": self.salary,
            "spending_patterns": self.spending_patterns,
        }


def generate_random_timestamp(base_date: datetime, user_info: UserInfo) -> datetime:
    """Generate a random timestamp within the given date."""
    # Generate random time components
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    microsecond = random.randint(0, 999999)

    user_tz = user_info.get_timezone()
    local_time = base_date.replace(
        hour=hour, minute=minute, second=second, microsecond=microsecond
    )

    return user_tz.localize(local_time)


def generate_events(
    user_info: UserInfo,
    days: int = 30,
    seed: int | None = None,
) -> EventCollection:
    """Generate a sequence of financial events for a user. All amounts are int cents."""
    events = EventCollection()

    # Set seed for deterministic generation
    if seed is not None:
        random.seed(seed)

    # Generate events for the specified number of days
    start_date = datetime.now() - timedelta(days=days)

    # Calculate bi-weekly paycheck amount (int cents)
    biweekly_pay = int(round(user_info.salary * 100 / 26))  # 26 pay periods per year

    current_date = start_date
    while current_date <= datetime.now():
        # Generate paycheck every 2 weeks
        if (
            current_date.weekday() == 4 and current_date.day % 14 < 7
        ):  # Every other Friday
            timestamp = generate_random_timestamp(current_date, user_info)
            events.events.append(
                create_paycheck_event(
                    user_id=user_info.user_id,
                    account_id=user_info.account_id,
                    amount=biweekly_pay,
                    timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    employer=user_info.employer,
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
                timestamp = generate_random_timestamp(current_date, user_info)
                events.events.append(
                    create_card_swipe_event(
                        user_id=user_info.user_id,
                        account_id=user_info.account_id,
                        amount=-amount,  # Negative for spending
                        timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        merchant=merchant,
                        category=category,
                        description=f"Purchase at {merchant}",
                    )
                )

        current_date += timedelta(days=1)

    return events


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.days <= 0:
        raise ValueError("Days must be positive")

    if args.format not in ["json", "binary"]:
        raise ValueError("Output format must be 'json' or 'binary'")


def main() -> None:
    """Main CLI entry point."""
    # Configure logging to show INFO level messages by default
    configure_logging(module_name="bedrock")

    logger = logging.getLogger(__name__)
    logger.info("Starting Bedrock CLI")

    parser = argparse.ArgumentParser(
        description="Bedrock - Generate realistic financial events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate --user-id 0042 --days 30 --output events.json
  %(prog)s generate --user-id 0042 --days 365 --seed 42 --format binary
  %(prog)s validate events.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate financial events"
    )
    generate_parser.add_argument("--user-id", required=True, help="User ID for events")
    generate_parser.add_argument(
        "--account-id", required=True, help="Account ID for events"
    )
    generate_parser.add_argument(
        "--timezone", default="US/Pacific", help="User timezone (default: US/Pacific)"
    )
    generate_parser.add_argument(
        "--employer", default="Acme Corp", help="Employer name (default: Acme Corp)"
    )
    generate_parser.add_argument(
        "--salary", type=float, default=65000.0, help="Annual salary (default: 65000)"
    )
    generate_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to generate (default: 30)",
    )
    generate_parser.add_argument(
        "--seed", type=int, help="Random seed for deterministic generation"
    )
    generate_parser.add_argument("--output", type=Path, help="Output file path")
    generate_parser.add_argument(
        "--format",
        choices=["json", "binary"],
        default="json",
        help="Output format (default: json)",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate event file")
    validate_parser.add_argument("file", type=Path, help="Event file to validate")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            validate_args(args)
            logger.info(f"Generating events for user {args.user_id}")

            # Create user info object
            user_info = UserInfo(
                user_id=args.user_id,
                account_id=args.account_id,
                timezone_name=args.timezone,
                employer=args.employer,
                salary=args.salary,
            )

            print(f"Generating {args.days} days of events for user {args.user_id}...")
            print(f"  Timezone: {args.timezone}")
            print(f"  Employer: {args.employer}")
            print(f"  Annual Salary: ${args.salary:,.2f}")

            events = generate_events(
                user_info=user_info,
                days=args.days,
                seed=args.seed,
            )

            logger.info(f"Generated {len(events.events)} events")

            if args.output:
                if args.format == "json":
                    save_json(events, args.output)
                else:
                    save_binary(events, args.output)
                logger.info(f"Saved events to {args.output}")
                print(f"Generated {len(events.events)} events, saved to {args.output}")
            else:
                # Output to stdout
                if args.format == "json":
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".json", delete=False
                    ) as f:
                        save_json(events, Path(f.name))
                        with open(f.name) as f2:
                            print(f2.read())
                else:
                    print("Output to stdout only supported for JSON format")

        elif args.command == "validate":
            logger.info(f"Validating file: {args.file}")
            if not args.file.exists():
                print(f"Error: File {args.file} does not exist", file=sys.stderr)
                sys.exit(1)

            try:
                if args.format == "json":
                    events = load_json(args.file, EventCollection)
                else:
                    events = load_binary(args.file, EventCollection)
                summary = get_event_summary(events.events)

                logger.info(f"Successfully validated {summary['total']} events")
                print(f"Validated {summary['total']} events in {args.file}")
                print("Event type distribution:")
                for event_type, count in summary.items():
                    if event_type != "total":
                        print(f"  {event_type}: {count}")

            except Exception as e:
                logger.error(f"Failed to validate file {args.file}: {e}")
                print(f"Error: Invalid file {args.file}: {e}", file=sys.stderr)
                sys.exit(1)

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
