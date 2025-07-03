"""
ID parsing and construction utilities for the DoppelBank hierarchical ID system.

This module implements the ID encoding scheme for wire IDs (string format used in APIs):
- User Wire IDs: user_{random_id} or client-provided string
- Item Wire IDs: {user_id}-{persona_id}-{institution_id}
- Account Wire IDs: {item_id}-{account_type}

Wire IDs are the string format used "on the wire" in APIs, files, etc.
They should be converted to structured ID objects immediately at boundaries.

All wire ID sections use only alphanumeric characters and underscores.
Hyphens are used as delimiters between sections.
"""

import re
import uuid
from dataclasses import dataclass


class InvalidIdError(ValueError):
    """Raised when an ID is malformed or invalid."""


@dataclass(frozen=True)
class UserId:
    """Structured User ID with parsed components."""

    user_id: str

    def __post_init__(self) -> None:
        _validate_section(self.user_id, "User ID")

    def to_wire(self) -> str:
        """Convert to wire ID format."""
        return self.user_id

    @staticmethod
    def from_wire(wire_id: str) -> "UserId":
        return UserId(user_id=wire_id)


@dataclass(frozen=True)
class ItemId:
    """Structured Item ID with parsed components."""

    user_id: str
    persona_id: str
    institution_id: str

    def __post_init__(self) -> None:
        _validate_section(self.user_id, "User ID")
        _validate_section(self.persona_id, "Persona ID")
        _validate_section(self.institution_id, "Institution ID")

    def to_wire(self) -> str:
        return f"{self.user_id}-{self.persona_id}-{self.institution_id}"

    @staticmethod
    def from_wire(wire_id: str) -> "ItemId":
        parts = wire_id.split("-")
        if len(parts) != 3:
            raise InvalidIdError(
                f"Item wire ID '{wire_id}' must have exactly 3 parts separated by hyphens"
            )

        user_id, persona_id, institution_id = parts
        return ItemId(
            user_id=user_id, persona_id=persona_id, institution_id=institution_id
        )

    def create_access_token(self) -> str:
        """Create a new access token for this item."""
        return f"{self.to_wire()}|{uuid.uuid4().hex}"

    @staticmethod
    def from_access_token(access_token: str) -> "ItemId":
        """Extract ItemId from access token format: {item_id}|{uuid}"""
        # item_id|uuid
        match = re.match(r"^([a-zA-Z0-9_-]+)\|([a-z0-9-]+)$", access_token)
        if not match:
            raise InvalidIdError(
                f"Access token '{access_token}' must have format 'item_id|uuid'"
            )

        item_id_part, uuid_part = match.groups()
        return ItemId.from_wire(item_id_part)


@dataclass(frozen=True)
class AccountId:
    """Structured Account ID with parsed components."""

    user_id: str
    persona_id: str
    institution_id: str
    account_type: str

    def __post_init__(self) -> None:
        _validate_section(self.user_id, "User ID")
        _validate_section(self.persona_id, "Persona ID")
        _validate_section(self.institution_id, "Institution ID")
        _validate_section(self.account_type, "Account type")

    @property
    def item_id(self) -> ItemId:
        return ItemId(
            user_id=self.user_id,
            persona_id=self.persona_id,
            institution_id=self.institution_id,
        )

    def to_wire(self) -> str:
        """Convert to wire ID format."""
        return f"{self.user_id}-{self.persona_id}-{self.institution_id}-{self.account_type}"

    @staticmethod
    def from_wire(wire_id: str) -> "AccountId":
        """Create from wire ID string."""
        parts = wire_id.split("-")
        if len(parts) != 4:
            raise InvalidIdError(
                f"Account wire ID '{wire_id}' must have exactly 4 parts separated by hyphens"
            )

        user_id, persona_id, institution_id, account_type = parts
        return AccountId(
            user_id=user_id,
            persona_id=persona_id,
            institution_id=institution_id,
            account_type=account_type,
        )


# Valid characters pattern: alphanumeric and underscores only
_VALID_SECTION_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _validate_section(contents: str, section_name: str) -> None:
    """Validate that a section contains only valid characters."""
    if not contents:
        raise InvalidIdError(f"{section_name} cannot be empty")
    if not _VALID_SECTION_PATTERN.match(contents):
        raise InvalidIdError(
            f"{section_name} '{contents}' contains invalid characters. "
            f"Only alphanumeric characters and underscores are allowed."
        )
