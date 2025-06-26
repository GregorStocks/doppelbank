from datetime import datetime
from typing import Optional

def parse_iso8601_z(ts: str) -> datetime:
    """Parse an ISO8601 string (with or without 'Z') to a datetime object."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def format_iso8601_z(dt: datetime) -> str:
    """Format a datetime object to ISO8601 string with 'Z' (UTC) and microseconds."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ") 