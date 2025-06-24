import argparse
from pathlib import Path
from doppelbank.lib import serde
from generated.bedrock import EventCollection
from generated.detritus import BankLedger, BankEvent, AddPending, AddCleared
import uuid
from datetime import datetime, timedelta

# Note: All betterproto messages implement the ProtoCollection protocol methods,
# but the type checker may not recognize this. We use type: ignore to silence false positives.

def to_microsecond_iso8601(ts: str) -> str:
    # Accepts ISO8601 string, returns microsecond-precision ISO8601 string
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def bedrock_to_detritus(bedrock_collection: EventCollection) -> BankLedger:
    events = []
    for event in bedrock_collection.events:
        # Only handle card swipes for now
        if event.card_swipe:
            cs = event.card_swipe
            # TODO: This is a hack. Skipping events with no timestamp is not robust; should validate bedrock events earlier and report errors instead of silently skipping.
            if not cs.timestamp:
                continue  # skip events with empty timestamp
            # AddPending event
            pending_id = str(uuid.uuid4())
            events.append(BankEvent(
                event_id=pending_id,
                timestamp=to_microsecond_iso8601(cs.timestamp),
                add_pending=AddPending(
                    event_id=pending_id,
                    transaction_id=str(uuid.uuid4()),
                    account_id="acc_dummy",
                    amount=cs.amount,  # already int cents
                    description=cs.description,
                    merchant=cs.merchant,
                    category=cs.category,
                )
            ))
            # AddCleared event (simulate clearing 2 days later)
            cleared_id = str(uuid.uuid4())
            cleared_dt = datetime.fromisoformat(cs.timestamp.replace("Z", "+00:00"))
            cleared_dt = cleared_dt.replace(microsecond=0)  # ensure microsecond precision
            cleared_dt = cleared_dt + timedelta(days=2)
            events.append(BankEvent(
                event_id=cleared_id,
                timestamp=cleared_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                add_cleared=AddCleared(
                    event_id=cleared_id,
                    transaction_id=str(uuid.uuid4()),
                    account_id="acc_dummy",
                    amount=cs.amount,  # already int cents
                    description=cs.description,
                    merchant=cs.merchant,
                    category=cs.category,
                    pending_event_id=pending_id,
                )
            ))
    # TODO: Not yet handling RemovePending or UpdateBalance BankEvent types from the detritus proto. Implement these as needed for full ledger support.
    return BankLedger(events=events)

def main():
    parser = argparse.ArgumentParser(description="Detritus - Generate Plaid-style sync data from bedrock events")
    parser.add_argument("--input", required=True, type=Path, help="Input bedrock events file (json or binary)")
    parser.add_argument("--output", required=True, type=Path, help="Output detritus ledger file (json or binary)")
    parser.add_argument("--format", choices=["json", "binary"], default="json", help="Output format")
    args = parser.parse_args()

    # TODO: CSV output is not supported for detritus yet. Implement CSV serialization if needed.

    # Load bedrock events
    if args.input.suffix == ".json":
        bedrock_collection = serde.load_json(args.input, EventCollection)  # type: ignore
    elif args.input.suffix == ".bin":
        bedrock_collection = serde.load_binary(args.input, EventCollection)  # type: ignore
    else:
        raise ValueError("Unsupported input format")

    # Transform
    detritus_ledger = bedrock_to_detritus(bedrock_collection)  # type: ignore

    # Save detritus ledger file
    if args.format == "json":
        serde.save_json(detritus_ledger, args.output)  # type: ignore
    else:
        serde.save_binary(detritus_ledger, args.output)  # type: ignore
    print(f"Wrote detritus ledger file to {args.output}")

if __name__ == "__main__":
    main()
