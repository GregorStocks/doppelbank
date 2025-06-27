"""
Generic serialization/deserialization utilities for msgspec models.
Handles JSON and binary msgpack for any msgspec Struct.
"""

from pathlib import Path

import msgspec


def save_json(collection: msgspec.Struct, file_path: Path) -> None:
    """Save a msgspec Struct to JSON file."""
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
