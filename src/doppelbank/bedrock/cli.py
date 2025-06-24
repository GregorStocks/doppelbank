#!/usr/bin/env python3
"""
Bedrock CLI - Simulates the "real world" financial events.

Generates structured, human-readable events such as paychecks, transfers,
card-swipes, etc. that represent real-world financial activities.
"""

# Standard library
import argparse
import json
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local project
from doppelbank.bedrock.models import (
    create_paycheck_event,
    create_transfer_event,
    create_card_swipe_event,
    save_events,
    save_events_json,
    load_events,
    get_event_summary
)


class UserInfo:
    """User information for generating personalized financial events."""
    
    def __init__(
        self,
        user_id: str,
        timezone_name: str = "US/Pacific",
        employer: str = "Acme Corp",
        salary: float = 65000.0,
        spending_patterns: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.timezone_name = timezone_name
        self.employer = employer
        self.salary = salary
        self.spending_patterns = spending_patterns or {}
    
    def get_timezone(self):
        """Get the timezone object for this user."""
        try:
            import pytz
            return pytz.timezone(self.timezone_name)
        except ImportError:
            # Fallback to UTC if pytz is not available
            return timezone.utc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user info to dictionary."""
        return {
            "user_id": self.user_id,
            "timezone_name": self.timezone_name,
            "employer": self.employer,
            "salary": self.salary,
            "spending_patterns": self.spending_patterns
        }


def generate_random_timestamp(base_date: datetime, user_info: UserInfo) -> datetime:
    """Generate a random timestamp within a given date in the user's timezone."""
    # Random hour between 6 AM and 10 PM
    hour = random.randint(6, 22)
    # Random minute
    minute = random.randint(0, 59)
    # Random second
    second = random.randint(0, 59)
    # Random microsecond
    microsecond = random.randint(0, 999999)
    
    # Create timestamp in user's timezone
    user_tz = user_info.get_timezone()
    local_time = base_date.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
    
    # Try to use pytz if available, otherwise fallback to basic timezone
    try:
        import pytz
        # Check if this is a pytz timezone object
        if 'pytz' in str(type(user_tz)):
            return user_tz.localize(local_time)  # type: ignore
    except ImportError:
        pass
    
    # Fallback to basic timezone assignment
    return local_time.replace(tzinfo=user_tz)


def generate_events(
    user_info: UserInfo,
    months: int = 12,
    seed: Optional[int] = None,
    output_format: str = "json"
) -> List[Any]:
    """Generate a sequence of financial events for a user."""
    events = []
    
    # Set seed for deterministic generation
    if seed is not None:
        random.seed(seed)
    
    # Generate events for the specified number of months
    start_date = datetime.now() - timedelta(days=months * 30)
    
    # Calculate bi-weekly paycheck amount
    biweekly_pay = user_info.salary / 26  # 26 pay periods per year
    
    current_date = start_date
    while current_date <= datetime.now():
        # Generate paycheck every 2 weeks
        if current_date.weekday() == 4 and current_date.day % 14 < 7:  # Every other Friday
            timestamp = generate_random_timestamp(current_date, user_info)
            events.append(create_paycheck_event(
                user_id=user_info.user_id,
                amount=biweekly_pay,
                timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                employer=user_info.employer,
                description="Bi-weekly paycheck"
            ))
        
        # Generate some random card swipes
        if current_date.weekday() < 5:  # Weekdays
            merchants = ["Starbucks", "Subway", "CVS", "Target", "Amazon"]
            categories = ["Food & Drink", "Shopping", "Transportation", "Entertainment"]
            
            for _ in range(2):  # 2 purchases per weekday
                merchant = random.choice(merchants)
                category = random.choice(categories)
                amount = random.uniform(5.0, 50.0)
                timestamp = generate_random_timestamp(current_date, user_info)
                events.append(create_card_swipe_event(
                    user_id=user_info.user_id,
                    amount=-amount,  # Negative for spending
                    timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    merchant=merchant,
                    category=category,
                    description=f"Purchase at {merchant}"
                ))
        
        current_date += timedelta(days=1)
    
    return events


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.months <= 0:
        raise ValueError("Months must be positive")
    
    if args.format not in ["json", "csv", "binary", "textproto"]:
        raise ValueError("Output format must be 'json', 'csv', 'binary', or 'textproto'")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bedrock - Generate realistic financial events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate --user-id 0042 --months 12 --output events.json
  %(prog)s generate --user-id 0042 --months 6 --seed 42 --format csv
  %(prog)s validate events.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate financial events")
    generate_parser.add_argument("--user-id", required=True, help="User ID for events")
    generate_parser.add_argument("--timezone", default="US/Pacific", help="User timezone (default: US/Pacific)")
    generate_parser.add_argument("--employer", default="Acme Corp", help="Employer name (default: Acme Corp)")
    generate_parser.add_argument("--salary", type=float, default=65000.0, help="Annual salary (default: 65000)")
    generate_parser.add_argument("--months", type=int, default=12, help="Number of months to generate (default: 12)")
    generate_parser.add_argument("--seed", type=int, help="Random seed for deterministic generation")
    generate_parser.add_argument("--output", type=Path, help="Output file path")
    generate_parser.add_argument("--format", choices=["json", "csv", "binary", "textproto"], default="json", help="Output format (default: json)")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate event file")
    validate_parser.add_argument("file", type=Path, help="Event file to validate")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show information about event types")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "generate":
            validate_args(args)
            
            # Create user info object
            user_info = UserInfo(
                user_id=args.user_id,
                timezone_name=args.timezone,
                employer=args.employer,
                salary=args.salary
            )
            
            print(f"Generating {args.months} months of events for user {args.user_id}...")
            print(f"  Timezone: {args.timezone}")
            print(f"  Employer: {args.employer}")
            print(f"  Annual Salary: ${args.salary:,.2f}")
            
            events = generate_events(
                user_info=user_info,
                months=args.months,
                seed=args.seed,
                output_format=args.format
            )
            
            if args.output:
                save_events(events, args.output, args.format)
                print(f"Generated {len(events)} events, saved to {args.output}")
            else:
                # Output to stdout
                if args.format == "json":
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        save_events_json(events, Path(f.name))
                        with open(f.name, 'r') as f2:
                            print(f2.read())
                else:
                    print("Output to stdout only supported for JSON format")
        
        elif args.command == "validate":
            if not args.file.exists():
                print(f"Error: File {args.file} does not exist", file=sys.stderr)
                sys.exit(1)
            
            try:
                events = load_events(args.file)
                summary = get_event_summary(events)
                
                print(f"Validated {summary['total']} events in {args.file}")
                print("Event type distribution:")
                for event_type, count in summary.items():
                    if event_type != 'total':
                        print(f"  {event_type}: {count}")
                    
            except Exception as e:
                print(f"Error: Invalid file {args.file}: {e}", file=sys.stderr)
                sys.exit(1)
        
        elif args.command == "info":
            print("Bedrock generates the following event types:")
            print()
            print("  paycheck    - Regular income from employment")
            print("  transfer    - Money movement between accounts")
            print("  card_swipe  - Credit/debit card transactions")
            print()
            print("Each event includes:")
            print("  - event_type: Type of financial event")
            print("  - user_id: Unique identifier for the user")
            print("  - amount: Transaction amount (positive for income, negative for spending)")
            print("  - timestamp: ISO format timestamp in user's timezone")
            print("  - description: Human-readable description")
            print("  - Additional fields specific to event type")
            print()
            print("User configuration options:")
            print("  - timezone: User's timezone (default: US/Pacific)")
            print("  - employer: Employer name for paycheck events")
            print("  - salary: Annual salary for calculating paycheck amounts")
            print()
            print("Supported output formats:")
            print("  - json: Human-readable JSON")
            print("  - csv: Comma-separated values")
            print("  - binary: Compact binary protobuf")
            print("  - textproto: Human-readable protobuf text format")
    
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
