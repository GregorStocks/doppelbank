"""
Data models for bedrock financial events using protobuf.

This module provides utilities for working with protobuf-generated event classes
and serialization/deserialization in various formats.
"""

# Standard library
import csv
import json
from pathlib import Path
from typing import List, Union

# Third-party
from google.protobuf import text_format
from google.protobuf.json_format import MessageToJson, Parse

# Local project
from doppelbank.bedrock.generated import events_pb2


def create_paycheck_event(
    user_id: str,
    amount: float,
    timestamp: str,
    employer: str,
    description: str = "Bi-weekly paycheck"
) -> events_pb2.Event:
    """Create a paycheck event."""
    event = events_pb2.Event()
    event.paycheck.user_id = user_id
    event.paycheck.amount = amount
    event.paycheck.timestamp = timestamp
    event.paycheck.employer = employer
    event.paycheck.description = description
    return event


def create_transfer_event(
    user_id: str,
    amount: float,
    timestamp: str,
    from_account: str,
    to_account: str,
    description: str = ""
) -> events_pb2.Event:
    """Create a transfer event."""
    event = events_pb2.Event()
    event.transfer.user_id = user_id
    event.transfer.amount = amount
    event.transfer.timestamp = timestamp
    event.transfer.from_account = from_account
    event.transfer.to_account = to_account
    event.transfer.description = description or f"Transfer from {from_account} to {to_account}"
    return event


def create_card_swipe_event(
    user_id: str,
    amount: float,
    timestamp: str,
    merchant: str,
    category: str,
    description: str = ""
) -> events_pb2.Event:
    """Create a card swipe event."""
    event = events_pb2.Event()
    event.card_swipe.user_id = user_id
    event.card_swipe.amount = amount
    event.card_swipe.timestamp = timestamp
    event.card_swipe.merchant = merchant
    event.card_swipe.category = category
    event.card_swipe.description = description or f"Purchase at {merchant}"
    return event


def save_events_binary(events: List[events_pb2.Event], file_path: Path) -> None:
    """Save events as binary protobuf."""
    collection = events_pb2.EventCollection()
    collection.events.extend(events)
    
    with open(file_path, 'wb') as f:
        f.write(collection.SerializeToString())


def save_events_json(events: List[events_pb2.Event], file_path: Path) -> None:
    """Save events as JSON."""
    collection = events_pb2.EventCollection()
    collection.events.extend(events)
    
    json_str = MessageToJson(collection, indent=2)
    with open(file_path, 'w') as f:
        f.write(json_str)


def save_events_textproto(events: List[events_pb2.Event], file_path: Path) -> None:
    """Save events as textproto (human-readable protobuf format)."""
    collection = events_pb2.EventCollection()
    collection.events.extend(events)
    
    text_str = text_format.MessageToString(collection)
    with open(file_path, 'w') as f:
        f.write(text_str)


def save_events_csv(events: List[events_pb2.Event], file_path: Path) -> None:
    """Save events as CSV (flattened format)."""
    if not events:
        return
    
    # Determine fieldnames based on the first event
    fieldnames = []
    sample_event = events[0]
    
    if sample_event.HasField('paycheck'):
        fieldnames = ['event_type', 'user_id', 'amount', 'timestamp', 'employer', 'description']
    elif sample_event.HasField('transfer'):
        fieldnames = ['event_type', 'user_id', 'amount', 'timestamp', 'from_account', 'to_account', 'description']
    elif sample_event.HasField('card_swipe'):
        fieldnames = ['event_type', 'user_id', 'amount', 'timestamp', 'merchant', 'category', 'description']
    
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            row = {'event_type': event.WhichOneof('event_data')}
            
            if event.HasField('paycheck'):
                row.update({
                    'user_id': event.paycheck.user_id,
                    'amount': event.paycheck.amount,
                    'timestamp': event.paycheck.timestamp,
                    'employer': event.paycheck.employer,
                    'description': event.paycheck.description,
                })
            elif event.HasField('transfer'):
                row.update({
                    'user_id': event.transfer.user_id,
                    'amount': event.transfer.amount,
                    'timestamp': event.transfer.timestamp,
                    'from_account': event.transfer.from_account,
                    'to_account': event.transfer.to_account,
                    'description': event.transfer.description,
                })
            elif event.HasField('card_swipe'):
                row.update({
                    'user_id': event.card_swipe.user_id,
                    'amount': event.card_swipe.amount,
                    'timestamp': event.card_swipe.timestamp,
                    'merchant': event.card_swipe.merchant,
                    'category': event.card_swipe.category,
                    'description': event.card_swipe.description,
                })
            
            writer.writerow(row)


def load_events_binary(file_path: Path) -> List[events_pb2.Event]:
    """Load events from binary protobuf file."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    collection = events_pb2.EventCollection()
    collection.ParseFromString(data)
    return list(collection.events)


def load_events_json(file_path: Path) -> List[events_pb2.Event]:
    """Load events from JSON file."""
    with open(file_path, 'r') as f:
        json_str = f.read()
    
    collection = Parse(json_str, events_pb2.EventCollection())
    return list(collection.events)


def load_events_textproto(file_path: Path) -> List[events_pb2.Event]:
    """Load events from textproto file."""
    with open(file_path, 'r') as f:
        text_str = f.read()
    
    collection = text_format.Parse(text_str, events_pb2.EventCollection())
    return list(collection.events)


def load_events_csv(file_path: Path) -> List[events_pb2.Event]:
    """Load events from CSV file."""
    events = []
    
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_type = row.get('event_type', '')
            
            if event_type == 'paycheck':
                event = create_paycheck_event(
                    user_id=row['user_id'],
                    amount=float(row['amount']),
                    timestamp=row['timestamp'],
                    employer=row['employer'],
                    description=row['description']
                )
            elif event_type == 'transfer':
                event = create_transfer_event(
                    user_id=row['user_id'],
                    amount=float(row['amount']),
                    timestamp=row['timestamp'],
                    from_account=row['from_account'],
                    to_account=row['to_account'],
                    description=row['description']
                )
            elif event_type == 'card_swipe':
                event = create_card_swipe_event(
                    user_id=row['user_id'],
                    amount=float(row['amount']),
                    timestamp=row['timestamp'],
                    merchant=row['merchant'],
                    category=row['category'],
                    description=row['description']
                )
            else:
                raise ValueError(f"Unknown event type: {event_type}")
            
            events.append(event)
    
    return events


def save_events(events: List[events_pb2.Event], file_path: Path, format: str = "json") -> None:
    """Save events to a file in the specified format."""
    if format == "binary":
        save_events_binary(events, file_path)
    elif format == "json":
        save_events_json(events, file_path)
    elif format == "textproto":
        save_events_textproto(events, file_path)
    elif format == "csv":
        save_events_csv(events, file_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_events(file_path: Union[str, Path]) -> List[events_pb2.Event]:
    """Load events from a file, automatically detecting format."""
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.bin':
        return load_events_binary(file_path)
    elif file_path.suffix.lower() == '.json':
        return load_events_json(file_path)
    elif file_path.suffix.lower() == '.textproto':
        return load_events_textproto(file_path)
    elif file_path.suffix.lower() == '.csv':
        return load_events_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def get_event_summary(events: List[events_pb2.Event]) -> dict:
    """Get a summary of event types and counts."""
    summary = {
        'paycheck': 0,
        'transfer': 0,
        'card_swipe': 0,
        'total': len(events)
    }
    
    for event in events:
        if event.HasField('paycheck'):
            summary['paycheck'] += 1
        elif event.HasField('transfer'):
            summary['transfer'] += 1
        elif event.HasField('card_swipe'):
            summary['card_swipe'] += 1
    
    return summary 