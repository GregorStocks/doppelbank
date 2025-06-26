"""
Generic serialization/deserialization utilities for betterproto models.
Handles JSON and binary protobuf for any generated collection.
"""
from pathlib import Path
from typing import Type, Self, Protocol, TypeVar

from betterproto import Message

T = TypeVar('T', bound=Message)

def save_json(collection: Message, file_path: Path) -> None:
    with open(file_path, "w") as f:
        f.write(collection.to_json(indent=2))


def load_json(file_path: Path, collection_type: Type[T]) -> T:
    with open(file_path, "r") as f:
        json_str = f.read()
    collection = collection_type()
    collection.from_json(json_str)
    return collection


def save_binary(collection: Message, file_path: Path) -> None:
    with open(file_path, "wb") as f:
        f.write(bytes(collection))


def load_binary(file_path: Path, collection_type: Type[T]) -> T:
    with open(file_path, "rb") as f:
        data = f.read()
    collection = collection_type()
    collection.parse(data)
    return collection