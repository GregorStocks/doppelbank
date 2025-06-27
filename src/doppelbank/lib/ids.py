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
from dataclasses import dataclass


class InvalidIdError(ValueError):
    """Raised when an ID is malformed or invalid."""


@dataclass(frozen=True)
class UserId:
    """Structured User ID with parsed components."""

    user_id: str

    def to_wire(self) -> str:
        """Convert to wire ID format."""
        return self.user_id


@dataclass(frozen=True)
class ItemId:
    """Structured Item ID with parsed components."""

    user_id: str
    persona_id: str
    institution_id: str

    def to_wire(self) -> str:
        """Convert to wire ID format."""
        return f"{self.user_id}-{self.persona_id}-{self.institution_id}"


@dataclass(frozen=True)
class AccountId:
    """Structured Account ID with parsed components."""

    user_id: str
    persona_id: str
    institution_id: str
    account_type: str

    @property
    def item_id(self) -> ItemId:
        """Get the Item ID portion of this account ID."""
        return ItemId(
            user_id=self.user_id,
            persona_id=self.persona_id,
            institution_id=self.institution_id,
        )

    def to_wire(self) -> str:
        """Convert to wire ID format."""
        return f"{self.user_id}-{self.persona_id}-{self.institution_id}-{self.account_type}"


# Valid characters pattern: alphanumeric and underscores only
_VALID_SECTION_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _validate_section(section: str, section_name: str) -> None:
    """Validate that a section contains only valid characters."""
    if not section:
        raise InvalidIdError(f"{section_name} cannot be empty")
    if not _VALID_SECTION_PATTERN.match(section):
        raise InvalidIdError(
            f"{section_name} '{section}' contains invalid characters. "
            f"Only alphanumeric characters and underscores are allowed."
        )


def parse_wire_user_id(wire_id: str) -> UserId:
    """
    Parse a User wire ID string into a structured User ID.

    Args:
        wire_id: The user wire ID string to parse

    Returns:
        UserId object with parsed components

    Raises:
        InvalidIdError: If the wire ID is malformed

    Examples:
        >>> parse_wire_user_id("user_abc123")
        UserId(user_id='user_abc123')
        >>> parse_wire_user_id("client_user_john_doe")
        UserId(user_id='client_user_john_doe')
    """
    if not wire_id:
        raise InvalidIdError("User wire ID cannot be empty")

    _validate_section(wire_id, "User wire ID")
    return UserId(user_id=wire_id)


def parse_wire_item_id(wire_id: str) -> ItemId:
    """
    Parse an Item wire ID string into a structured Item ID.

    Args:
        wire_id: The item wire ID string to parse

    Returns:
        ItemId object with parsed components

    Raises:
        InvalidIdError: If the wire ID is malformed

    Examples:
        >>> parse_wire_item_id("user_abc123-jimmy-doppelbank")
        ItemId(user_id='user_abc123', persona_id='jimmy', institution_id='doppelbank')
    """
    if not wire_id:
        raise InvalidIdError("Item wire ID cannot be empty")

    parts = wire_id.split("-")
    if len(parts) != 3:
        raise InvalidIdError(
            f"Item wire ID '{wire_id}' must have exactly 3 parts separated by hyphens. "
            f"Expected format: user_id-persona_id-institution_id"
        )

    user_id, persona_id, institution_id = parts

    _validate_section(user_id, "User ID")
    _validate_section(persona_id, "Persona ID")
    _validate_section(institution_id, "Institution ID")

    return ItemId(user_id=user_id, persona_id=persona_id, institution_id=institution_id)


def parse_wire_account_id(wire_id: str) -> AccountId:
    """
    Parse an Account wire ID string into a structured Account ID.

    Args:
        wire_id: The account wire ID string to parse

    Returns:
        AccountId object with parsed components

    Raises:
        InvalidIdError: If the wire ID is malformed

    Examples:
        >>> parse_wire_account_id("user_abc123-jimmy-doppelbank-checking")
        AccountId(user_id='user_abc123', persona_id='jimmy',
                 institution_id='doppelbank', account_type='checking')
    """
    if not wire_id:
        raise InvalidIdError("Account wire ID cannot be empty")

    parts = wire_id.split("-")
    if len(parts) != 4:
        raise InvalidIdError(
            f"Account wire ID '{wire_id}' must have exactly 4 parts separated by hyphens. "
            f"Expected format: user_id-persona_id-institution_id-account_type"
        )

    user_id, persona_id, institution_id, account_type = parts

    _validate_section(user_id, "User ID")
    _validate_section(persona_id, "Persona ID")
    _validate_section(institution_id, "Institution ID")
    _validate_section(account_type, "Account type")

    return AccountId(
        user_id=user_id,
        persona_id=persona_id,
        institution_id=institution_id,
        account_type=account_type,
    )


def build_item_wire_id(user_id: str, persona_id: str, institution_id: str) -> str:
    """
    Build an Item wire ID from its components.

    Args:
        user_id: The user ID
        persona_id: The persona ID
        institution_id: The institution ID

    Returns:
        The constructed item wire ID string

    Raises:
        InvalidIdError: If any component is invalid

    Examples:
        >>> build_item_wire_id("user_abc123", "jimmy", "doppelbank")
        'user_abc123-jimmy-doppelbank'
    """
    _validate_section(user_id, "User ID")
    _validate_section(persona_id, "Persona ID")
    _validate_section(institution_id, "Institution ID")

    return f"{user_id}-{persona_id}-{institution_id}"


def build_account_wire_id(item_wire_id: str, account_type: str) -> str:
    """
    Build an Account wire ID from an item wire ID and account type.

    Args:
        item_wire_id: The item wire ID (will be validated by parsing)
        account_type: The account type

    Returns:
        The constructed account wire ID string

    Raises:
        InvalidIdError: If any component is invalid

    Examples:
        >>> build_account_wire_id("user_abc123-jimmy-doppelbank", "checking")
        'user_abc123-jimmy-doppelbank-checking'
    """
    # Validate the item_wire_id by parsing it
    parse_wire_item_id(item_wire_id)

    _validate_section(account_type, "Account type")

    return f"{item_wire_id}-{account_type}"


def build_account_wire_id_from_components(
    user_id: str, persona_id: str, institution_id: str, account_type: str
) -> str:
    """
    Build an Account wire ID directly from all components.

    Args:
        user_id: The user ID
        persona_id: The persona ID
        institution_id: The institution ID
        account_type: The account type

    Returns:
        The constructed account wire ID string

    Raises:
        InvalidIdError: If any component is invalid

    Examples:
        >>> build_account_wire_id_from_components("user_abc123", "jimmy", "doppelbank", "checking")
        'user_abc123-jimmy-doppelbank-checking'
    """
    _validate_section(user_id, "User ID")
    _validate_section(persona_id, "Persona ID")
    _validate_section(institution_id, "Institution ID")
    _validate_section(account_type, "Account type")

    return f"{user_id}-{persona_id}-{institution_id}-{account_type}"
