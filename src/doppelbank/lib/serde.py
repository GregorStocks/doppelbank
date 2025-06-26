"""
Generic serialization/deserialization utilities for betterproto models.
Handles JSON and binary protobuf for any generated collection.
"""

from pathlib import Path

from betterproto import Message


def save_json(collection: Message, file_path: Path) -> None:
    with open(file_path, "w") as f:
        f.write(collection.to_json(indent=2))


def load_json[T: Message](file_path: Path, collection_type: type[T]) -> T:
    with open(file_path) as f:
        json_str = f.read()
    collection = collection_type()
    collection.from_json(json_str)
    return collection


def save_binary(collection: Message, file_path: Path) -> None:
    with open(file_path, "wb") as f:
        f.write(bytes(collection))


def load_binary[T: Message](file_path: Path, collection_type: type[T]) -> T:
    with open(file_path, "rb") as f:
        data = f.read()
    collection = collection_type()
    collection.parse(data)
    return collection
