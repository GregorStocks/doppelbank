import argparse
from pathlib import Path

from doppelbank.detritus.transform import bedrock_to_detritus
from doppelbank.lib import serde
from doppelbank.lib.logging_config import configure_logging
from doppelbank.schemas.bedrock import EventCollection

# Note: All betterproto messages implement the ProtoCollection protocol methods,
# but the type checker may not recognize this. We use type: ignore to silence false positives.


def main() -> None:
    # Configure logging to show INFO level messages by default
    configure_logging(module_name="detritus")

    parser = argparse.ArgumentParser(
        description="Detritus - Generate Plaid-style sync data from bedrock events"
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input bedrock events file (json or binary)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output detritus ledger file (json or binary)",
    )
    parser.add_argument(
        "--format", choices=["json", "binary"], default="json", help="Output format"
    )
    args = parser.parse_args()

    # Load bedrock events
    if args.input.suffix == ".json":
        bedrock_collection = serde.load_json(args.input, EventCollection)
    elif args.input.suffix == ".bin":
        bedrock_collection = serde.load_binary(args.input, EventCollection)
    else:
        raise ValueError("Unsupported input format")

    # Transform
    detritus_ledger = bedrock_to_detritus(bedrock_collection)

    # Save detritus ledger file
    if args.format == "json":
        serde.save_json(detritus_ledger, args.output)
    else:
        serde.save_binary(detritus_ledger, args.output)
    print(f"Wrote detritus ledger file to {args.output}")


if __name__ == "__main__":
    main()
