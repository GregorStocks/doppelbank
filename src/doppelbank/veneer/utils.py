import os
from pathlib import Path

from doppelbank.lib.ids import AccountId


def get_data_dir() -> Path:
    """Get the data directory, configurable via environment variable."""
    data_dir = Path(os.environ.get("VENEER_DATA_DIR", "tests/data/detritus"))
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_hierarchical_data_dir() -> Path:
    """Get the hierarchical data directory."""
    return Path(os.environ.get("VENEER_HIERARCHICAL_DATA_DIR", "data"))


def find_account_file(account_id: str) -> Path:
    """Find account data file using hierarchical ID structure or fallback to flat structure."""
    # First try hierarchical structure
    try:
        hierarchical_root = get_hierarchical_data_dir()
        if hierarchical_root.exists():
            # Try to parse as hierarchical account ID
            try:
                parsed_account = AccountId.from_wire(account_id)
                account_file = (
                    hierarchical_root
                    / "personas"
                    / parsed_account.persona_id
                    / parsed_account.institution_id
                    / f"{parsed_account.account_type}.json"
                )
                if account_file.exists():
                    return account_file
            except Exception:
                pass  # Fall through to flat structure search

            # Search in hierarchical structure for exact match
            personas_dir = hierarchical_root / "personas"
            if personas_dir.exists():
                for persona_dir in personas_dir.iterdir():
                    if persona_dir.is_dir():
                        for institution_dir in persona_dir.iterdir():
                            if institution_dir.is_dir():
                                for account_file in institution_dir.glob("*.json"):
                                    # Check if this file contains the account ID we're looking for
                                    try:
                                        with open(account_file) as f:
                                            content = f.read()
                                            if (
                                                f'"account_id": "{account_id}"'
                                                in content
                                            ):
                                                return account_file
                                    except Exception:
                                        continue
    except Exception:
        pass
    # Fall back to flat structure
    flat_data_dir = get_data_dir()
    flat_file = flat_data_dir / f"{account_id}.json"
    return flat_file
