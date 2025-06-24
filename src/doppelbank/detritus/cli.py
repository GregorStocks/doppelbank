import argparse
from pathlib import Path
from doppelbank.lib import serde
from doppelbank.bedrock.generated.doppelbank.bedrock import EventCollection
from doppelbank.detritus.generated.doppelbank.detritus import (
    TransactionsSyncResponse, Transaction, Account
)

# Note: All betterproto messages implement the ProtoCollection protocol methods,
# but the type checker may not recognize this. We use type: ignore to silence false positives.

def bedrock_to_detritus(bedrock_collection: EventCollection) -> TransactionsSyncResponse:
    # Minimal transformation: just convert each bedrock event to a detritus Transaction
    transactions = []
    accounts = []
    for event in bedrock_collection.events:
        # For now, just create a dummy Transaction for each event
        transactions.append(
            Transaction(
                transaction_id=event.paycheck.user_id or event.transfer.user_id or event.card_swipe.user_id,
                account_id="acc_dummy",
                name=getattr(event, 'description', ""),
                amount=getattr(event, 'amount', 0.0),
                date="2024-01-01",
            )
        )
    # Dummy account
    accounts.append(Account(account_id="acc_dummy", name="Checking"))
    return TransactionsSyncResponse(
        added=transactions,
        modified=[],
        removed=[],
        accounts=accounts,
        next_cursor="dummy-cursor",
        has_more=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Detritus - Generate Plaid-style sync data from bedrock events")
    parser.add_argument("--input", required=True, type=Path, help="Input bedrock events file (json or binary)")
    parser.add_argument("--output", required=True, type=Path, help="Output detritus sync file (json or binary)")
    parser.add_argument("--format", choices=["json", "binary"], default="json", help="Output format")
    args = parser.parse_args()

    # Load bedrock events
    if args.input.suffix == ".json":
        bedrock_collection = serde.load_json(args.input, EventCollection)  # type: ignore
    elif args.input.suffix == ".bin":
        bedrock_collection = serde.load_binary(args.input, EventCollection)  # type: ignore
    else:
        raise ValueError("Unsupported input format")

    # Transform
    detritus_collection = bedrock_to_detritus(bedrock_collection)  # type: ignore

    # Save detritus sync file
    if args.format == "json":
        serde.save_json(detritus_collection, args.output)  # type: ignore
    else:
        serde.save_binary(detritus_collection, args.output)  # type: ignore
    print(f"Wrote detritus sync file to {args.output}")


if __name__ == "__main__":
    main()
