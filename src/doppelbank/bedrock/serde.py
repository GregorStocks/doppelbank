"""
Serialization and deserialization utilities for bedrock events.

This module handles converting events to/from various formats including
JSON, CSV, and binary protobuf.
"""

# Standard library
import csv
from pathlib import Path
from typing import List

# Local project
from generated.bedrock import (
    EventCollection, Event, PaycheckEvent, TransferEvent, CardSwipeEvent
)
from doppelbank.bedrock.models import (
    create_card_swipe_event,
    create_paycheck_event,
    create_transfer_event,
)


def save_events_binary(events: List[Event], file_path: Path) -> None:
    """Save events as binary protobuf."""
    collection = EventCollection()
    collection.events = events

    with open(file_path, "wb") as f:
        f.write(bytes(collection))


def save_events_json(events: List[Event], file_path: Path) -> None:
    """Save events as JSON."""
    collection = EventCollection()
    collection.events = events

    json_str = collection.to_json(indent=2)
    with open(file_path, "w") as f:
        f.write(json_str)


def save_events_csv(events: List[Event], file_path: Path) -> None:
    """Save events as CSV (flattened format)."""
    if not events:
        return

    # Convert to dict first, then flatten to CSV
    collection = EventCollection()
    collection.events = events
    dict_data = collection.to_dict()

    # Flatten the dict structure to CSV rows
    rows = []
    for event in dict_data.get("events", []):
        row = {"event_type": ""}

        # Check which event type is present and flatten it
        if "paycheck" in event:
            row["event_type"] = "paycheck"
            row.update(event["paycheck"])
        elif "transfer" in event:
            row["event_type"] = "transfer"
            row.update(event["transfer"])
        elif "cardSwipe" in event:  # Note: dict uses camelCase
            row["event_type"] = "card_swipe"
            row.update(event["cardSwipe"])
        else:
            continue  # Skip events with no data

        rows.append(row)

    if not rows:
        return

    # Get all possible field names from all rows
    all_fields: set[str] = set()
    for row in rows:
        all_fields.update(row.keys())

    # Sort fields for consistent column order
    fieldnames = sorted(list(all_fields))

    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_events_binary(file_path: Path) -> List[Event]:
    """Load events from binary protobuf file."""
    with open(file_path, "rb") as f:
        data = f.read()

    collection = EventCollection()
    collection.parse(data)
    return list(collection.events)


def load_events_json(file_path: Path) -> List[Event]:
    """Load events from JSON file."""
    with open(file_path, "r") as f:
        json_str = f.read()

    collection = EventCollection()
    collection.from_json(json_str)
    return list(collection.events)


def load_events_csv(file_path: Path) -> List[Event]:
    """Load events from CSV file."""
    events = []

    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_type = row.get("event_type", "")

            if event_type == "paycheck":
                event = create_paycheck_event(
                    user_id=row["userId"],  # Handle camelCase from dict
                    amount=int(row["amount"]),
                    timestamp=row["timestamp"],
                    employer=row["employer"],
                    description=row["description"],
                )
            elif event_type == "transfer":
                event = create_transfer_event(
                    user_id=row["userId"],  # Handle camelCase from dict
                    amount=int(row["amount"]),
                    timestamp=row["timestamp"],
                    from_account=row.get(
                        "fromAccount", ""
                    ),  # Handle camelCase from dict
                    to_account=row.get("toAccount", ""),  # Handle camelCase from dict
                    description=row["description"],
                )
            elif event_type == "card_swipe":
                event = create_card_swipe_event(
                    user_id=row["userId"],  # Handle camelCase from dict
                    amount=int(row["amount"]),
                    timestamp=row["timestamp"],
                    merchant=row["merchant"],
                    category=row["category"],
                    description=row["description"],
                )
            else:
                raise ValueError(f"Unknown event type: {event_type}")

            events.append(event)

    return events


def save_events(events: List[Event], file_path: Path, format: str = "json") -> None:
    """Save events to a file in the specified format."""
    if format == "binary":
        save_events_binary(events, file_path)
    elif format == "json":
        save_events_json(events, file_path)
    elif format == "csv":
        save_events_csv(events, file_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_events(file_path: Path) -> List[Event]:
    """Load events from a file, automatically detecting format."""
    if file_path.suffix.lower() == ".bin":
        return load_events_binary(file_path)
    elif file_path.suffix.lower() == ".json":
        return load_events_json(file_path)
    elif file_path.suffix.lower() == ".csv":
        return load_events_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
