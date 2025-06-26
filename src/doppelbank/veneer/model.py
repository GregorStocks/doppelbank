import os
from pathlib import Path


def get_data_dir() -> Path:
    """Get the data directory, configurable via environment variable."""
    data_dir = Path(os.environ.get("VENEER_DATA_DIR", "tests/data/detritus"))
    data_dir.mkdir(exist_ok=True)
    return data_dir
