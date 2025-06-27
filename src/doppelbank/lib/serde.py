"""
Generic serialization/deserialization utilities for msgspec models.
Handles JSON and binary msgpack for any msgspec Struct.
"""

import json
from pathlib import Path

import msgspec


def save_json(collection: msgspec.Struct, file_path: Path, pretty: bool = True) -> None:
    """Save a msgspec Struct to JSON file."""
    if pretty:
        # Use standard json library for pretty printing
        # First convert to dict using msgspec, then pretty print with json
        data = msgspec.to_builtins(collection)
        json_str = json.dumps(data, indent=2, sort_keys=False)
        with open(file_path, "w") as f:
            f.write(json_str)
    else:
        # Use msgspec for compact output
        json_bytes = msgspec.json.encode(collection)
        with open(file_path, "wb") as f:
            f.write(json_bytes)


def load_json[T](file_path: Path, collection_type: type[T]) -> T:
    """Load a msgspec Struct from JSON file."""
    with open(file_path, "rb") as f:
        json_bytes = f.read()
    return msgspec.json.decode(json_bytes, type=collection_type)


def save_binary(collection: msgspec.Struct, file_path: Path) -> None:
    """Save a msgspec Struct to binary msgpack file."""
    binary_data = msgspec.msgpack.encode(collection)
    with open(file_path, "wb") as f:
        f.write(binary_data)


def load_binary[T](file_path: Path, collection_type: type[T]) -> T:
    """Load a msgspec Struct from binary msgpack file."""
    with open(file_path, "rb") as f:
        binary_data = f.read()
    return msgspec.msgpack.decode(binary_data, type=collection_type)
