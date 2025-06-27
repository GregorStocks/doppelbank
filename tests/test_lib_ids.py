"""
Unit tests for ID parsing and construction utilities.
"""

import pytest

from doppelbank.lib.ids import (
    AccountId,
    InvalidIdError,
    ItemId,
    UserId,
    build_account_wire_id,
    build_account_wire_id_from_components,
    build_item_wire_id,
    parse_wire_account_id,
    parse_wire_item_id,
    parse_wire_user_id,
)


class TestUserId:
    """Test User ID parsing and validation."""

    def test_parse_valid_user_wire_id_simple(self) -> None:
        """Test parsing a simple user wire ID."""
        user_id = parse_wire_user_id("user_abc123")
        assert user_id.user_id == "user_abc123"
        assert user_id.to_wire() == "user_abc123"

    def test_parse_valid_user_wire_id_client_provided(self) -> None:
        """Test parsing a client-provided user wire ID."""
        user_id = parse_wire_user_id("client_user_john_doe")
        assert user_id.user_id == "client_user_john_doe"
        assert user_id.to_wire() == "client_user_john_doe"

    def test_parse_valid_user_wire_id_with_numbers(self) -> None:
        """Test parsing user wire ID with numbers."""
        user_id = parse_wire_user_id("user_123_abc_456")
        assert user_id.user_id == "user_123_abc_456"

    def test_parse_empty_user_wire_id(self) -> None:
        """Test parsing empty user wire ID raises error."""
        with pytest.raises(InvalidIdError, match="User wire ID cannot be empty"):
            parse_wire_user_id("")

    def test_parse_user_wire_id_with_hyphens(self) -> None:
        """Test parsing user wire ID with hyphens raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            parse_wire_user_id("user-with-hyphens")

    def test_parse_user_wire_id_with_spaces(self) -> None:
        """Test parsing user wire ID with spaces raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            parse_wire_user_id("user with spaces")

    def test_parse_user_wire_id_with_special_chars(self) -> None:
        """Test parsing user wire ID with special characters raises error."""
        with pytest.raises(InvalidIdError, match="contains invalid characters"):
            parse_wire_user_id("user@domain.com")


class TestItemId:
    """Test Item ID parsing and validation."""

    def test_parse_valid_item_wire_id(self) -> None:
        """Test parsing a valid item wire ID."""
        item_id = parse_wire_item_id("user_abc123-jimmy-doppelbank")
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"
        assert item_id.to_wire() == "user_abc123-jimmy-doppelbank"

    def test_parse_valid_item_wire_id_client_user(self) -> None:
        """Test parsing item wire ID with client user."""
        item_id = parse_wire_item_id("client_user-claude-doppelfirstbank")
        assert item_id.user_id == "client_user"
        assert item_id.persona_id == "claude"
        assert item_id.institution_id == "doppelfirstbank"

    def test_parse_valid_item_wire_id_complex(self) -> None:
        """Test parsing item wire ID with complex names."""
        item_id = parse_wire_item_id("user_xyz789-john_doe-second_bank_of_doppel")
        assert item_id.user_id == "user_xyz789"
        assert item_id.persona_id == "john_doe"
        assert item_id.institution_id == "second_bank_of_doppel"

    def test_parse_empty_item_wire_id(self) -> None:
        """Test parsing empty item wire ID raises error."""
        with pytest.raises(InvalidIdError, match="Item wire ID cannot be empty"):
            parse_wire_item_id("")

    def test_parse_item_wire_id_too_few_parts(self) -> None:
        """Test parsing item wire ID with too few parts raises error."""
        with pytest.raises(
            InvalidIdError, match="must have exactly 3 parts separated by hyphens"
        ):
            parse_wire_item_id("user_abc123-jimmy")

    def test_parse_item_wire_id_too_many_parts(self) -> None:
        """Test parsing item wire ID with too many parts raises error."""
        with pytest.raises(
            InvalidIdError, match="must have exactly 3 parts separated by hyphens"
        ):
            parse_wire_item_id("user_abc123-jimmy-doppelbank-extra")

    def test_parse_item_wire_id_empty_section(self) -> None:
        """Test parsing item wire ID with empty section raises error."""
        with pytest.raises(InvalidIdError, match="cannot be empty"):
            parse_wire_item_id("user_abc123--doppelbank")

    def test_parse_item_wire_id_invalid_user_section(self) -> None:
        """Test parsing item wire ID with invalid user section raises error."""
        with pytest.raises(
            InvalidIdError, match="User ID.*contains invalid characters"
        ):
            parse_wire_item_id("user@domain-jimmy-doppelbank")

    def test_parse_item_wire_id_invalid_persona_section(self) -> None:
        """Test parsing item wire ID with invalid persona section raises error."""
        with pytest.raises(
            InvalidIdError, match="Persona ID.*contains invalid characters"
        ):
            parse_wire_item_id("user_abc123-jimmy!-doppelbank")

    def test_parse_item_wire_id_invalid_institution_section(self) -> None:
        """Test parsing item wire ID with invalid institution section raises error."""
        with pytest.raises(
            InvalidIdError, match="Institution ID.*contains invalid characters"
        ):
            parse_wire_item_id("user_abc123-jimmy-doppel bank")


class TestAccountId:
    """Test Account ID parsing and validation."""

    def test_parse_valid_account_wire_id(self) -> None:
        """Test parsing a valid account wire ID."""
        account_id = parse_wire_account_id("user_abc123-jimmy-doppelbank-checking")
        assert account_id.user_id == "user_abc123"
        assert account_id.persona_id == "jimmy"
        assert account_id.institution_id == "doppelbank"
        assert account_id.account_type == "checking"
        assert account_id.to_wire() == "user_abc123-jimmy-doppelbank-checking"

    def test_parse_valid_account_wire_id_complex(self) -> None:
        """Test parsing account wire ID with complex names."""
        account_id = parse_wire_account_id("user_xyz789-john_doe-second_bank-checking2")
        assert account_id.user_id == "user_xyz789"
        assert account_id.persona_id == "john_doe"
        assert account_id.institution_id == "second_bank"
        assert account_id.account_type == "checking2"

    def test_account_id_item_id_property(self) -> None:
        """Test the item_id property of AccountId."""
        account_id = parse_wire_account_id("user_abc123-jimmy-doppelbank-checking")
        item_id = account_id.item_id
        assert isinstance(item_id, ItemId)
        assert item_id.user_id == "user_abc123"
        assert item_id.persona_id == "jimmy"
        assert item_id.institution_id == "doppelbank"

    def test_parse_empty_account_wire_id(self) -> None:
        """Test parsing empty account wire ID raises error."""
        with pytest.raises(InvalidIdError, match="Account wire ID cannot be empty"):
            parse_wire_account_id("")

    def test_parse_account_wire_id_too_few_parts(self) -> None:
        """Test parsing account wire ID with too few parts raises error."""
        with pytest.raises(
            InvalidIdError, match="must have exactly 4 parts separated by hyphens"
        ):
            parse_wire_account_id("user_abc123-jimmy-doppelbank")

    def test_parse_account_wire_id_too_many_parts(self) -> None:
        """Test parsing account wire ID with too many parts raises error."""
        with pytest.raises(
            InvalidIdError, match="must have exactly 4 parts separated by hyphens"
        ):
            parse_wire_account_id("user_abc123-jimmy-doppelbank-checking-extra")

    def test_parse_account_wire_id_empty_section(self) -> None:
        """Test parsing account wire ID with empty section raises error."""
        with pytest.raises(InvalidIdError, match="cannot be empty"):
            parse_wire_account_id("user_abc123-jimmy-doppelbank-")

    def test_parse_account_wire_id_invalid_account_type(self) -> None:
        """Test parsing account wire ID with invalid account type raises error."""
        with pytest.raises(
            InvalidIdError, match="Account type.*contains invalid characters"
        ):
            parse_wire_account_id("user_abc123-jimmy-doppelbank-checking!")


class TestBuildItemWireId:
    """Test Item wire ID building functionality."""

    def test_build_valid_item_wire_id(self) -> None:
        """Test building a valid item wire ID."""
        item_wire_id = build_item_wire_id("user_abc123", "jimmy", "doppelbank")
        assert item_wire_id == "user_abc123-jimmy-doppelbank"

    def test_build_item_wire_id_complex_names(self) -> None:
        """Test building item wire ID with complex names."""
        item_wire_id = build_item_wire_id(
            "user_xyz789", "john_doe", "second_bank_of_doppel"
        )
        assert item_wire_id == "user_xyz789-john_doe-second_bank_of_doppel"

    def test_build_item_wire_id_empty_user_id(self) -> None:
        """Test building item wire ID with empty user ID raises error."""
        with pytest.raises(InvalidIdError, match="User ID cannot be empty"):
            build_item_wire_id("", "jimmy", "doppelbank")

    def test_build_item_wire_id_empty_persona_id(self) -> None:
        """Test building item wire ID with empty persona ID raises error."""
        with pytest.raises(InvalidIdError, match="Persona ID cannot be empty"):
            build_item_wire_id("user_abc123", "", "doppelbank")

    def test_build_item_wire_id_empty_institution_id(self) -> None:
        """Test building item wire ID with empty institution ID raises error."""
        with pytest.raises(InvalidIdError, match="Institution ID cannot be empty"):
            build_item_wire_id("user_abc123", "jimmy", "")

    def test_build_item_wire_id_invalid_user_id(self) -> None:
        """Test building item wire ID with invalid user ID raises error."""
        with pytest.raises(
            InvalidIdError, match="User ID.*contains invalid characters"
        ):
            build_item_wire_id("user-with-hyphens", "jimmy", "doppelbank")

    def test_build_item_wire_id_invalid_persona_id(self) -> None:
        """Test building item wire ID with invalid persona ID raises error."""
        with pytest.raises(
            InvalidIdError, match="Persona ID.*contains invalid characters"
        ):
            build_item_wire_id("user_abc123", "jimmy!", "doppelbank")

    def test_build_item_wire_id_invalid_institution_id(self) -> None:
        """Test building item wire ID with invalid institution ID raises error."""
        with pytest.raises(
            InvalidIdError, match="Institution ID.*contains invalid characters"
        ):
            build_item_wire_id("user_abc123", "jimmy", "doppel bank")


class TestBuildAccountWireId:
    """Test Account wire ID building functionality."""

    def test_build_valid_account_wire_id(self) -> None:
        """Test building a valid account wire ID from item wire ID."""
        account_wire_id = build_account_wire_id(
            "user_abc123-jimmy-doppelbank", "checking"
        )
        assert account_wire_id == "user_abc123-jimmy-doppelbank-checking"

    def test_build_account_wire_id_complex_names(self) -> None:
        """Test building account wire ID with complex names."""
        account_wire_id = build_account_wire_id(
            "user_xyz789-john_doe-second_bank", "checking2"
        )
        assert account_wire_id == "user_xyz789-john_doe-second_bank-checking2"

    def test_build_account_wire_id_invalid_item_wire_id(self) -> None:
        """Test building account wire ID with invalid item wire ID raises error."""
        with pytest.raises(
            InvalidIdError, match="must have exactly 3 parts separated by hyphens"
        ):
            build_account_wire_id("invalid-item", "checking")

    def test_build_account_wire_id_empty_account_type(self) -> None:
        """Test building account wire ID with empty account type raises error."""
        with pytest.raises(InvalidIdError, match="Account type cannot be empty"):
            build_account_wire_id("user_abc123-jimmy-doppelbank", "")

    def test_build_account_wire_id_invalid_account_type(self) -> None:
        """Test building account wire ID with invalid account type raises error."""
        with pytest.raises(
            InvalidIdError, match="Account type.*contains invalid characters"
        ):
            build_account_wire_id("user_abc123-jimmy-doppelbank", "checking!")


class TestBuildAccountWireIdFromComponents:
    """Test Account wire ID building from all components."""

    def test_build_valid_account_wire_id_from_components(self) -> None:
        """Test building a valid account wire ID from all components."""
        account_wire_id = build_account_wire_id_from_components(
            "user_abc123", "jimmy", "doppelbank", "checking"
        )
        assert account_wire_id == "user_abc123-jimmy-doppelbank-checking"

    def test_build_account_wire_id_from_components_complex(self) -> None:
        """Test building account wire ID from complex components."""
        account_wire_id = build_account_wire_id_from_components(
            "user_xyz789", "john_doe", "second_bank_of_doppel", "savings_premium"
        )
        assert (
            account_wire_id
            == "user_xyz789-john_doe-second_bank_of_doppel-savings_premium"
        )

    def test_build_account_wire_id_from_components_empty_user_id(self) -> None:
        """Test building account wire ID with empty user ID raises error."""
        with pytest.raises(InvalidIdError, match="User ID cannot be empty"):
            build_account_wire_id_from_components("", "jimmy", "doppelbank", "checking")

    def test_build_account_wire_id_from_components_invalid_persona_id(self) -> None:
        """Test building account wire ID with invalid persona ID raises error."""
        with pytest.raises(
            InvalidIdError, match="Persona ID.*contains invalid characters"
        ):
            build_account_wire_id_from_components(
                "user_abc123", "jimmy-invalid", "doppelbank", "checking"
            )

    def test_build_account_wire_id_from_components_invalid_account_type(self) -> None:
        """Test building account wire ID with invalid account type raises error."""
        with pytest.raises(
            InvalidIdError, match="Account type.*contains invalid characters"
        ):
            build_account_wire_id_from_components(
                "user_abc123", "jimmy", "doppelbank", "checking@type"
            )


class TestRoundTripParsing:
    """Test round-trip parsing and building of wire IDs."""

    def test_item_wire_id_round_trip(self) -> None:
        """Test that parsing and building item wire IDs is reversible."""
        original = "user_abc123-jimmy-doppelbank"
        parsed = parse_wire_item_id(original)
        rebuilt = build_item_wire_id(
            parsed.user_id, parsed.persona_id, parsed.institution_id
        )
        assert rebuilt == original
        assert parsed.to_wire() == original

    def test_account_wire_id_round_trip(self) -> None:
        """Test that parsing and building account wire IDs is reversible."""
        original = "user_abc123-jimmy-doppelbank-checking"
        parsed = parse_wire_account_id(original)
        rebuilt = build_account_wire_id_from_components(
            parsed.user_id,
            parsed.persona_id,
            parsed.institution_id,
            parsed.account_type,
        )
        assert rebuilt == original
        assert parsed.to_wire() == original


class TestDataclassProperties:
    """Test properties and behavior of dataclasses."""

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
