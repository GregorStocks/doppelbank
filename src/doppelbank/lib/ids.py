"""
ID parsing and construction utilities for the DoppelBank hierarchical ID system.

This module implements the ID encoding scheme for wire IDs (string format used in APIs):
- User Wire IDs: user:{user_id}
- Item Wire IDs: item:{user_id}-{persona_id}-{institution_id}
- Account Wire IDs: account:{user_id}-{persona_id}-{institution_id}-{account_type}

Wire IDs are the string format used "on the wire" in APIs, files, etc.
They should be converted to structured ID objects immediately at boundaries.

All wire ID sections use only alphanumeric characters and underscores.
Hyphens are used as delimiters between sections, colons separate the prefix from the ID.
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
        return f"user:{self.user_id}"

    def __str__(self) -> str:
        return self.to_wire()

    @staticmethod
    def from_wire(wire_id: str) -> "UserId":
        """Parse a user wire ID string into a UserId object."""
        match = _USER_WIRE_PATTERN.match(wire_id)
        if not match:
            raise InvalidIdError(
                f"User wire ID '{wire_id}' must have format 'user:{{user_id}}' "
                f"where user_id contains only alphanumeric characters and underscores"
            )

        user_id = match.group(1)
        return UserId(user_id=user_id)


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
        return f"item:{self.user_id}-{self.persona_id}-{self.institution_id}"

    def __str__(self) -> str:
        return self.to_wire()

    @staticmethod
    def from_wire(wire_id: str) -> "ItemId":
        """Parse an item wire ID string into an ItemId object."""
        match = _ITEM_WIRE_PATTERN.match(wire_id)
        if not match:
            raise InvalidIdError(
                f"Item wire ID '{wire_id}' must have format "
                f"'item:{{user_id}}-{{persona_id}}-{{institution_id}}' "
                f"where all components contain only alphanumeric characters and underscores"
            )

        user_id, persona_id, institution_id = match.groups()
        return ItemId(user_id=user_id, persona_id=persona_id, institution_id=institution_id)

    def create_access_token(self) -> str:
        """Create a new access token for this item."""
        return f"token:{self.user_id}-{self.persona_id}-{self.institution_id}-{uuid.uuid4().hex}"

    @staticmethod
    def from_access_token(access_token: str) -> "ItemId":
        """Extract ItemId from access token."""
        match = _ACCESS_TOKEN_PATTERN.match(access_token)
        if not match:
            raise InvalidIdError(
                f"Access token '{access_token}' must have format "
                f"'token:{{user_id}}-{{persona_id}}-{{institution_id}}-{{uuid}}'"
            )

        user_id, persona_id, institution_id, uuid_part = match.groups()
        return ItemId(user_id=user_id, persona_id=persona_id, institution_id=institution_id)


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
        return f"account:{self.user_id}-{self.persona_id}-{self.institution_id}-{self.account_type}"

    def __str__(self) -> str:
        return self.to_wire()

    @staticmethod
    def from_wire(wire_id: str) -> "AccountId":
        """Parse an account wire ID string into an AccountId object."""
        match = _ACCOUNT_WIRE_PATTERN.match(wire_id)
        if not match:
            raise InvalidIdError(
                f"Account wire ID '{wire_id}' must have format "
                f"'account:{{user_id}}-{{persona_id}}-{{institution_id}}-{{account_type}}' "
                f"where all components contain only alphanumeric characters and underscores"
            )

        user_id, persona_id, institution_id, account_type = match.groups()
        return AccountId(
            user_id=user_id,
            persona_id=persona_id,
            institution_id=institution_id,
            account_type=account_type,
        )


# Regex patterns for parsing wire IDs with embedded comments

# Valid characters for ID sections: alphanumeric and underscores only
_VALID_SECTION_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

# User wire ID pattern: user:{user_id}
_USER_WIRE_PATTERN = re.compile(
    r"""
    ^
    user:                    # Literal 'user:' prefix
    ([a-zA-Z0-9_]+)         # Group 1: user_id (alphanumeric and underscores)
    $
""",
    re.VERBOSE,
)

# Item wire ID pattern: item:{user_id}-{persona_id}-{institution_id}
_ITEM_WIRE_PATTERN = re.compile(
    r"""
    ^
    item:                   # Literal 'item:' prefix
    ([a-zA-Z0-9_]+)        # Group 1: user_id
    -                      # Hyphen separator
    ([a-zA-Z0-9_]+)        # Group 2: persona_id
    -                      # Hyphen separator
    ([a-zA-Z0-9_]+)        # Group 3: institution_id
    $
""",
    re.VERBOSE,
)

# Account wire ID pattern: account:{user_id}-{persona_id}-{institution_id}-{account_type}
_ACCOUNT_WIRE_PATTERN = re.compile(
    r"""
    ^
    account:               # Literal 'account:' prefix
    ([a-zA-Z0-9_]+)       # Group 1: user_id
    -                     # Hyphen separator
    ([a-zA-Z0-9_]+)       # Group 2: persona_id
    -                     # Hyphen separator
    ([a-zA-Z0-9_]+)       # Group 3: institution_id
    -                     # Hyphen separator
    ([a-zA-Z0-9_]+)       # Group 4: account_type
    $
""",
    re.VERBOSE,
)

# Access token pattern: token:{user_id}-{persona_id}-{institution_id}-{uuid}
_ACCESS_TOKEN_PATTERN = re.compile(
    r"""
    ^
    token:                 # Literal 'token:' prefix
    ([a-zA-Z0-9_]+)       # Group 1: user_id
    -                     # Hyphen separator
    ([a-zA-Z0-9_]+)       # Group 2: persona_id
    -                     # Hyphen separator
    ([a-zA-Z0-9_]+)       # Group 3: institution_id
    -                     # Hyphen separator
    ([a-z0-9]+)           # Group 4: UUID (lowercase hex without hyphens)
    $
""",
    re.VERBOSE,
)


def _validate_section(contents: str, section_name: str) -> None:
    """Validate that a section contains only valid characters."""
    if not contents:
        raise InvalidIdError(f"{section_name} cannot be empty")
    if not _VALID_SECTION_PATTERN.match(contents):
        raise InvalidIdError(
            f"{section_name} '{contents}' contains invalid characters. "
            f"Only alphanumeric characters and underscores are allowed."
        )
