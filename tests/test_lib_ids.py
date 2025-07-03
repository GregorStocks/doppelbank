"""
Unit tests for ID parsing and construction utilities.
"""

import pytest

from doppelbank.lib.ids import (
    AccountId,
    InvalidIdError,
    ItemId,
    UserId,
)


class TestUserId:
    """Test User ID parsing and validation."""

    def test_from_wire_valid_simple(self) -> None:
        """Test creating from a simple user wire ID."""
        user_id = UserId.from_wire("user_abc123")
        assert user_id.user_id == "user_abc123"
        assert user_id.to_wire() == "user_abc123"

    def test_from_wire_valid_client_provided(self) -> None:
        """Test creating from a client-provided user wire ID."""
        user_id = UserId.from_wire("client_user_john_doe")
        assert user_id.user_id == "client_user_john_doe"
        assert user_id.to_wire() == "client_user_john_doe"

    def test_from_wire_valid_with_numbers(self) -> None:
        """Test creating from user wire ID with numbers."""
        user_id = UserId.from_wire("user_123_abc_456")
        assert user_id.user_id == "user_123_abc_456"

    def test_from_wire_with_hyphens(self) -> None:
        """Test creating from user wire ID with hyphens raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            UserId.from_wire("user-with-hyphens")

    def test_from_wire_with_spaces(self) -> None:
        """Test creating from user wire ID with spaces raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            UserId.from_wire("user with spaces")

    def test_from_wire_with_special_chars(self) -> None:
        """Test creating from user wire ID with special characters raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            UserId.from_wire("user@domain.com")

    def test_constructor_validation(self) -> None:
        """Test direct constructor validates input."""
        with pytest.raises(InvalidIdError, match="User ID cannot be empty"):
            UserId("")

    def test_constructor_valid(self) -> None:
        """Test direct constructor with valid input."""
        user_id = UserId("user_abc123")
        assert user_id.user_id == "user_abc123"


class TestItemId:
    """Test Item ID parsing and validation."""

    def test_from_wire_valid(self) -> None:
        """Test creating from a valid item wire ID."""
        item_id = ItemId.from_wire("user_abc123-jimmy-doppelbank")
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"
        assert item_id.to_wire() == "user_abc123-jimmy-doppelbank"

    def test_from_wire_client_user(self) -> None:
        """Test creating from item wire ID with client user."""
        item_id = ItemId.from_wire("client_user-claude-doppelfirstbank")
        assert item_id.user_id == "client_user"
        assert item_id.persona_id == "claude"
        assert item_id.institution_id == "doppelfirstbank"

    def test_from_wire_complex(self) -> None:
        """Test creating from item wire ID with complex names."""
        item_id = ItemId.from_wire("user_xyz789-john_doe-second_bank_of_doppel")
        assert item_id.user_id == "user_xyz789"
        assert item_id.persona_id == "john_doe"
        assert item_id.institution_id == "second_bank_of_doppel"

    def test_from_wire_too_few_parts(self) -> None:
        """Test creating from item wire ID with too few parts raises error."""
        with pytest.raises(InvalidIdError, match="must have exactly 3 parts separated by hyphens"):
            ItemId.from_wire("user_abc123-jimmy")

    def test_from_wire_too_many_parts(self) -> None:
        """Test creating from item wire ID with too many parts raises error."""
        with pytest.raises(InvalidIdError, match="must have exactly 3 parts separated by hyphens"):
            ItemId.from_wire("user_abc123-jimmy-doppelbank-extra")

    def test_from_wire_empty_section(self) -> None:
        """Test creating from item wire ID with empty section raises error."""
        with pytest.raises(InvalidIdError, match="cannot be empty"):
            ItemId.from_wire("user_abc123--doppelbank")

    def test_from_wire_invalid_user_section(self) -> None:
        """Test creating from item wire ID with invalid user section raises error."""
        with pytest.raises(InvalidIdError, match="User ID.*contains invalid characters"):
            ItemId.from_wire("user@domain-jimmy-doppelbank")

    def test_from_wire_invalid_persona_section(self) -> None:
        """Test creating from item wire ID with invalid persona section raises error."""
        with pytest.raises(InvalidIdError, match="Persona ID.*contains invalid characters"):
            ItemId.from_wire("user_abc123-jimmy!-doppelbank")

    def test_from_wire_invalid_institution_section(self) -> None:
        """Test creating from item wire ID with invalid institution section raises error."""
        with pytest.raises(InvalidIdError, match="Institution ID.*contains invalid characters"):
            ItemId.from_wire("user_abc123-jimmy-doppel bank")

    def test_constructor_validation(self) -> None:
        """Test direct constructor validates input."""
        with pytest.raises(InvalidIdError, match="User ID.*contains invalid characters"):
            ItemId("user-invalid", "jimmy", "doppelbank")

    def test_constructor_valid(self) -> None:
        """Test direct constructor with valid input."""
        item_id = ItemId("user_abc123", "jimmy", "doppelbank")
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"


class TestAccountId:
    """Test Account ID parsing and validation."""

    def test_from_wire_valid(self) -> None:
        """Test creating from a valid account wire ID."""
        account_id = AccountId.from_wire("user_abc123-jimmy-doppelbank-checking")
        assert account_id.user_id == "user_abc123"
        assert account_id.persona_id == "jimmy"
        assert account_id.institution_id == "doppelbank"
        assert account_id.account_type == "checking"
        assert account_id.to_wire() == "user_abc123-jimmy-doppelbank-checking"

    def test_from_wire_complex(self) -> None:
        """Test creating from account wire ID with complex names."""
        account_id = AccountId.from_wire("user_xyz789-john_doe-second_bank-checking2")
        assert account_id.user_id == "user_xyz789"
        assert account_id.persona_id == "john_doe"
        assert account_id.institution_id == "second_bank"
        assert account_id.account_type == "checking2"

    def test_account_id_item_id_property(self) -> None:
        """Test the item_id property of AccountId."""
        account_id = AccountId.from_wire("user_abc123-jimmy-doppelbank-checking")
        item_id = account_id.item_id
        assert isinstance(item_id, ItemId)
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"

    def test_account_id_item_wire_id_property(self) -> None:
        """Test the item_wire_id property of AccountId."""
        account_id = AccountId.from_wire("user_abc123-jimmy-doppelbank-checking")
        assert account_id.item_id.to_wire() == "user_abc123-jimmy-doppelbank"

    def test_from_wire_too_few_parts(self) -> None:
        """Test creating from account wire ID with too few parts raises error."""
        with pytest.raises(InvalidIdError, match="must have exactly 4 parts separated by hyphens"):
            AccountId.from_wire("user_abc123-jimmy-doppelbank")

    def test_from_wire_too_many_parts(self) -> None:
        """Test creating from account wire ID with too many parts raises error."""
        with pytest.raises(InvalidIdError, match="must have exactly 4 parts separated by hyphens"):
            AccountId.from_wire("user_abc123-jimmy-doppelbank-checking-extra")

    def test_from_wire_empty_section(self) -> None:
        """Test creating from account wire ID with empty section raises error."""
        with pytest.raises(InvalidIdError, match="cannot be empty"):
            AccountId.from_wire("user_abc123-jimmy-doppelbank-")

    def test_from_wire_invalid_account_type(self) -> None:
        """Test creating from account wire ID with invalid account type raises error."""
        with pytest.raises(InvalidIdError, match="Account type.*contains invalid characters"):
            AccountId.from_wire("user_abc123-jimmy-doppelbank-checking!")

    def test_constructor_validation(self) -> None:
        """Test direct constructor validates input."""
        with pytest.raises(InvalidIdError, match="Account type.*contains invalid characters"):
            AccountId("user_abc123", "jimmy", "doppelbank", "checking!")

    def test_constructor_valid(self) -> None:
        """Test direct constructor with valid input."""
        account_id = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        assert account_id.user_id == "user_abc123"
        assert account_id.persona_id == "jimmy"
        assert account_id.institution_id == "doppelbank"
        assert account_id.account_type == "checking"


class TestConstructorBuilding:
    """Test building IDs with direct constructors."""

    def test_build_item_id_with_constructor(self) -> None:
        """Test building an item ID with constructor."""
        item_id = ItemId("user_abc123", "jimmy", "doppelbank")
        assert item_id.to_wire() == "user_abc123-jimmy-doppelbank"

    def test_build_account_id_with_constructor(self) -> None:
        """Test building an account ID with constructor."""
        account_id = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        assert account_id.to_wire() == "user_abc123-jimmy-doppelbank-checking"

    def test_build_account_id_from_item_id(self) -> None:
        """Test building account ID from existing item ID."""
        item_id = ItemId("user_abc123", "jimmy", "doppelbank")
        account_id = AccountId(
            item_id.user_id, item_id.persona_id, item_id.institution_id, "checking"
        )
        assert account_id.to_wire() == "user_abc123-jimmy-doppelbank-checking"


class TestRoundTripParsing:
    """Test round-trip parsing and building of wire IDs."""

    def test_item_wire_id_round_trip(self) -> None:
        """Test that parsing and building item wire IDs is reversible."""
        original = "user_abc123-jimmy-doppelbank"
        parsed = ItemId.from_wire(original)
        assert parsed.to_wire() == original

    def test_account_wire_id_round_trip(self) -> None:
        """Test that parsing and building account wire IDs is reversible."""
        original = "user_abc123-jimmy-doppelbank-checking"
        parsed = AccountId.from_wire(original)
        assert parsed.to_wire() == original

    def test_account_wire_id_round_trip_via_item_wire_id(self) -> None:
        """Test building account wire ID via item wire ID property."""
        original = "user_abc123-jimmy-doppelbank-checking"
        parsed = AccountId.from_wire(original)
        # Can reconstruct from item_wire_id + account_type
        rebuilt_wire_id = f"{parsed.item_id.to_wire()}-{parsed.account_type}"
        assert rebuilt_wire_id == original


class TestDataclassProperties:
    """Test properties and behavior of dataclasses."""

    def test_user_id_frozen(self) -> None:
        """Test that UserId dataclass is frozen."""
        user_id = UserId("user_abc123")
        with pytest.raises(AttributeError):
            user_id.user_id = "different"  # type: ignore

    def test_item_id_frozen(self) -> None:
        """Test that ItemId dataclass is frozen."""
        item_id = ItemId("user_abc123", "jimmy", "doppelbank")
        with pytest.raises(AttributeError):
            item_id.user_id = "different"  # type: ignore

    def test_account_id_frozen(self) -> None:
        """Test that AccountId dataclass is frozen."""
        account_id = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        with pytest.raises(AttributeError):
            account_id.user_id = "different"  # type: ignore

    def test_dataclass_equality(self) -> None:
        """Test that dataclasses with same values are equal."""
        user_id1 = UserId("user_abc123")
        user_id2 = UserId("user_abc123")
        assert user_id1 == user_id2

        item_id1 = ItemId("user_abc123", "jimmy", "doppelbank")
        item_id2 = ItemId("user_abc123", "jimmy", "doppelbank")
        assert item_id1 == item_id2

        account_id1 = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        account_id2 = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        assert account_id1 == account_id2


class TestToWireMethods:
    """Test to_wire() methods on dataclasses."""

    def test_user_id_to_wire(self) -> None:
        """Test UserId.to_wire() method."""
        user_id = UserId("user_abc123")
        assert user_id.to_wire() == "user_abc123"

    def test_item_id_to_wire(self) -> None:
        """Test ItemId.to_wire() method."""
        item_id = ItemId("user_abc123", "jimmy", "doppelbank")
        assert item_id.to_wire() == "user_abc123-jimmy-doppelbank"

    def test_account_id_to_wire(self) -> None:
        """Test AccountId.to_wire() method."""
        account_id = AccountId("user_abc123", "jimmy", "doppelbank", "checking")
        assert account_id.to_wire() == "user_abc123-jimmy-doppelbank-checking"


class TestFromWireMethods:
    """Test from_wire() static methods."""

    def test_user_id_from_wire(self) -> None:
        """Test UserId.from_wire static method."""
        user_id = UserId.from_wire("user_abc123")
        assert isinstance(user_id, UserId)
        assert user_id.user_id == "user_abc123"

    def test_item_id_from_wire(self) -> None:
        """Test ItemId.from_wire static method."""
        item_id = ItemId.from_wire("user_abc123-jimmy-doppelbank")
        assert isinstance(item_id, ItemId)
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"

    def test_account_id_from_wire(self) -> None:
        """Test AccountId.from_wire static method."""
        account_id = AccountId.from_wire("user_abc123-jimmy-doppelbank-checking")
        assert isinstance(account_id, AccountId)
        assert account_id.user_id == "user_abc123"
        assert account_id.persona_id == "jimmy"
        assert account_id.institution_id == "doppelbank"
        assert account_id.account_type == "checking"


class TestValidationEdgeCases:
    """Test edge cases for validation."""

    def test_empty_components_caught_by_constructor(self) -> None:
        """Test that empty components are caught by constructor validation."""
        with pytest.raises(InvalidIdError, match="User ID cannot be empty"):
            ItemId("", "jimmy", "doppelbank")

        with pytest.raises(InvalidIdError, match="Persona ID cannot be empty"):
            ItemId("user_abc123", "", "doppelbank")

        with pytest.raises(InvalidIdError, match="Institution ID cannot be empty"):
            ItemId("user_abc123", "jimmy", "")

    def test_invalid_characters_caught_by_constructor(self) -> None:
        """Test that invalid characters are caught by constructor validation."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            ItemId("user-invalid", "jimmy", "doppelbank")

        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            ItemId("user_abc123", "jimmy!", "doppelbank")

        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            ItemId("user_abc123", "jimmy", "doppel bank")

    def test_complex_valid_ids(self) -> None:
        """Test complex but valid ID constructions."""
        # Complex user ID
        user_id = UserId("complex_client_user_name_123_with_underscores")
        assert user_id.to_wire() == "complex_client_user_name_123_with_underscores"

        # Complex item ID
        item_id = ItemId("user_123", "persona_name_with_underscores", "bank_name_2024")
        assert item_id.to_wire() == "user_123-persona_name_with_underscores-bank_name_2024"

        # Complex account ID
        account_id = AccountId("user_123", "persona_name", "bank_name", "savings_premium_2024")
        assert account_id.to_wire() == "user_123-persona_name-bank_name-savings_premium_2024"


class TestAccessTokenHelpers:
    """Test access token helper methods."""

    def test_create_access_token(self) -> None:
        """Test creating access token from ItemId."""
        item_id = ItemId("user_123", "jimmy", "doppelbank")
        access_token = item_id.create_access_token()

        # Should have format: {item_id}|{uuid}
        assert "|" in access_token
        parts = access_token.split("|")
        assert len(parts) == 2
        assert parts[0] == "user_123-jimmy-doppelbank"
        assert len(parts[1]) == 32  # UUID hex without dashes

    def test_from_access_token(self) -> None:
        """Test extracting ItemId from access token."""
        original_item = ItemId("user_123", "jimmy", "doppelbank")
        access_token = f"{original_item.to_wire()}|abc123def456"

        extracted_item = ItemId.from_access_token(access_token)
        assert extracted_item == original_item

    def test_access_token_round_trip(self) -> None:
        """Test round-trip: ItemId -> access_token -> ItemId."""
        original_item = ItemId("user_123", "jimmy", "doppelbank")
        access_token = original_item.create_access_token()
        extracted_item = ItemId.from_access_token(access_token)

        assert extracted_item == original_item

    def test_from_access_token_invalid_format(self) -> None:
        """Test that invalid access token format raises error."""
        with pytest.raises(InvalidIdError, match="must have format 'item_id|uuid'"):
            ItemId.from_access_token("invalid_token_without_separator")

    def test_from_access_token_invalid_item_id(self) -> None:
        """Test that invalid item ID in access token raises error."""
        with pytest.raises(InvalidIdError, match="must have exactly 3 parts"):
            ItemId.from_access_token("invalid-item|uuid")

    def test_from_access_token_multiple_separators(self) -> None:
        """Test access token with multiple separators raises error."""
        access_token = "user_123-jimmy-doppelbank|uuid|extra"

        with pytest.raises(InvalidIdError, match="must have format 'item_id|uuid'"):
            ItemId.from_access_token(access_token)


class TestStringificationProtection:
    """Test that ID objects cannot be accidentally stringified."""

    def test_user_id_str_raises_error(self) -> None:
        """Test that UserId.__str__ raises an error."""
        user_id = UserId("user_123")
        with pytest.raises(InvalidIdError, match="should not be stringified directly"):
            str(user_id)

    def test_item_id_str_raises_error(self) -> None:
        """Test that ItemId.__str__ raises an error."""
        item_id = ItemId("user_123", "jimmy", "doppelbank")
        with pytest.raises(InvalidIdError, match="should not be stringified directly"):
            str(item_id)

    def test_account_id_str_raises_error(self) -> None:
        """Test that AccountId.__str__ raises an error."""
        account_id = AccountId("user_123", "jimmy", "doppelbank", "checking")
        with pytest.raises(InvalidIdError, match="should not be stringified directly"):
            str(account_id)

    def test_item_id_f_string_raises_error(self) -> None:
        """Test that ItemId in f-string raises an error."""
        item_id = ItemId("user_123", "jimmy", "doppelbank")
        with pytest.raises(InvalidIdError, match="should not be stringified directly"):
            f"Account: {item_id}-checking"

    def test_to_wire_still_works(self) -> None:
        """Test that .to_wire() still works correctly."""
        user_id = UserId("user_123")
        item_id = ItemId("user_123", "jimmy", "doppelbank")
        account_id = AccountId("user_123", "jimmy", "doppelbank", "checking")

        assert user_id.to_wire() == "user_123"
        assert item_id.to_wire() == "user_123-jimmy-doppelbank"
        assert account_id.to_wire() == "user_123-jimmy-doppelbank-checking"
