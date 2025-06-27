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

- will be used to delimit different sections of the ID. The only valid characters in the sections will be alphanumeric and _.

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

TODO