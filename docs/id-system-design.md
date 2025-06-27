# ID System Design: Globally Unique Items and Accounts

## Problem Statement

Currently, DoppelBank uses simple, non-unique identifiers like `"test_account"` for both items and accounts. This causes confusion for external services that expect globally unique IDs, particularly:

- **Item IDs**: Should be unique across all users and institutions
- **Account IDs**: Should be unique across all items and account types
- **User isolation**: Different users should have completely separate namespaces

## Current System Issues

1. **Non-unique IDs**: `"test_account"` appears across multiple users
2. **Flat file structure**: `tests/data/detritus/test_account.json` doesn't encode user or item information
3. **Service confusion**: External APIs expect item/account IDs to be globally unique identifiers

## Proposed Solution

### Hierarchical ID System

```
User ID → Item ID → Account ID
   ↓        ↓          ↓
user_123  item_456   acct_789
```

### ID Encoding Schemes

Hyphens (`-`) will be used to delimit different sections of the ID. The only valid characters within the sections themselves will be alphanumeric and underscores (`_`).

Users will not be explicitly stored anywhere - we could have 500 different users that are views on the same 5 personas. Personas will be checked into the repo and have their own metadata (though probably not a lot of it.)

#### User IDs
- **Format**: `user_{random_id}` or client-provided string
- **Examples**: `user_abc123`, `client_user_john_doe`
- **Source**: Either randomly generated or provided by client applications

#### Item IDs  
- **Format**: `{user_id}_{persona_id}_{institution_id}`
- **Examples**: 
  - `user_abc123-jimmy-doppelbank`
  - `user_abc123-johndoe-secondbankofdoppel`
  - `client_user-claude-doppelfirstbank`
- **Reversible**: Can extract user_id, persona ID, and institution from item_id

#### Account IDs
- **Format**: `{item_id}_{account_id}`
- **Examples**:
  - `user_abc123-jimmy-doppelbank-checking`
  - `user_abc123-johndoe-secondbankofdoppel-checking2`
  - `client_user-claude-doppelfirstbank-cc`
- **Reversible**: Can extract item_id and account_type from account_id

### File System Layout

#### Current Structure
```
tests/data/detritus/
├── test_account.json
└── demo_account.json
```

#### Proposed Structure
```
data/
  personas/
    jimmy/
      persona.json
      doppelbank/
        checking.json
        savings.json
        cc.json
      second_bank_of_doppel/
        checking1.json
        checking2.json
  institutions/
    doppelbank.json
    second_bank_of_doppel.json
```

## High Level Changes

- We combine bedrock and detritus into a single service, persona-generator, which generates a new persona in data/personas. It won't take very many parameters for now. Ultimately it will be very configurable, so you can run it to generate a high-income spendthrift and then run it again with different parameters to generate a low-income disciplined person, etc. The data in personas/ will be pretty similar to what detritus outputs today. (We combine them because the bank-level information needs to be able to inform actual spending decisions, i.e. Jimmy gets an overdraft - Bedrock doesn't really have enough information to do that properly.)
- We add explicit persona.json metadata (generated based on inputs) and institution metadata (written by hand). One institution is fine for now, we'll add more later.
- We ensure that we're always passing the relevant IDs up and down the stack to respect what the user passed in. We get rid of all defaults, since those have bitten us a bunch - the default is "we return an error and our tests fail" so we know we're not done.
- We parse account IDs in the fancy new way when deciding what transactions to return, etc.
- We get rid of the Bedrock-only data types.

## Detailed implementation plan

1.  **Define ID Parsing Logic:**
    *   Create a utility module (e.g., `src/doppelbank/lib/ids.py`) to handle parsing and construction of User, Item, and Account IDs.
    *   Implement functions like `parse_user_id(id_string)`, `parse_item_id(id_string)`, `parse_account_id(id_string)` that return structured objects (e.g., dataclasses) containing the parsed components.
    *   Implement functions like `build_item_id(user_id, persona_id, institution_id)` and `build_account_id(item_id, account_type)` to construct IDs from their components.
    *   Ensure robust error handling for malformed IDs.
    *   **Unit Tests:** Add comprehensive unit tests for the new ID parsing and building utility functions (`src/doppelbank/lib/ids.py`).

2.  **Refactor Data Storage and Generation (Bedrock/Detritus - Persona Generator):**
    *   **New Data Directory Structure:** Create the `data/` directory at the project root.
    *   **Persona Data:**
        *   Modify the `persona-generator` (combination of bedrock and detritus) to generate persona data into `data/personas/{persona_name}/persona.json`.
        *   Update existing data generation scripts/logic to use the new ID and file system conventions.
    *   **Institution Data:**
        *   Create `data/institutions/{institution_name}.json` for institution metadata.
        *   Update any code that currently hardcodes institution details to read from these files.
    *   **Account Data:**
        *   Modify the `persona-generator` to store account data under `data/personas/{persona_name}/{institution_name}/{account_type}.json`.
        *   Update all data loading logic (e.g., in `src/doppelbank/veneer/endpoints/accounts.py`, `src/doppelbank/veneer/endpoints/transactions.py`) to traverse this new hierarchical structure and construct/parse IDs accordingly.
    *   **Data Cleanup and Regeneration:**
        *   All existing test data (`tests/data/detritus/test_account.json`, `tests/data/detritus/demo_account.json`, etc.) will be deleted.
        *   New persona and institution data will be generated from scratch using the updated `persona-generator` into the `data/` directory.
    *   **Integration Tests (Phase 1 - Bedrock/Detritus):** Focus on testing the `persona-generator`'s ability to create and manage persona data in the new `data/` directory structure. Ensure the generated data conforms to the new ID formats.

3.  **Update API Endpoints and Internal Logic (Veneer Service):**
    *   Review all endpoints in `src/doppelbank/veneer/endpoints/` (e.g., `accounts.py`, `transactions.py`, `link/public/link_token_create.py`, `link/public/public_token_exchange.py`) that deal with Item or Account IDs.
    *   Modify these endpoints to expect and return the new globally unique ID formats.
    *   Integrate the ID parsing/building utility functions.
    *   **Integration Tests (Phase 2 - Veneer):** Update existing integration tests (e.g., `tests/test_veneer_integration.py`, `tests/test_veneer_link.py`) to reflect the new ID formats and data storage, directly using the `data/personas` directory for test data.

4.  **Documentation:**
    *   Update any internal documentation or READMEs that describe the data structure or ID conventions.
    *   Ensure the `id-system-design.md` file is up-to-date with the final implementation details.
