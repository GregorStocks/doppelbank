# Doppel Bank

*"Spin up financial doppelgängers and pull their ledgers through a Plaid-compatible API."*

Doppel Bank is a developer sandbox that lets you test budgeting, cash-flow, and PFM ideas **without touching real money or PII**.

---

## Quick start (90 seconds)

```
git clone https://github.com/GregorStocks/doppelbank.git
cd doppelbank
uv sync --extra dev

# 1. Generate a new synthetic user (24 months, deterministic seed)
uv run python -m doppelbank.bedrock.cli generate --user-id 0042 --months 24 --seed 42 > personas/user_0042.json

# 2. Launch the Plaid-style sandbox (serves all personas)
uvicorn doppelbank.plaidshim.server:app --reload

# 3. Hit the endpoints (example with httpie)
http POST http://localhost:8000/link/token/create user_id=0042
http POST http://localhost:8000/transactions/sync access_token=demo-0042

# 4. Run tests
uv run pytest
```

## Architecture

Doppelbank has three major components.

**Bedrock** – Simulates the "real world." Emits structured, human-readable events, such as paychecks, transfers, card-swipes, etc.

**Detritus** – Simulates the bank. Converts bedrock events to a messier sequence of account-level events - messier merchant strings/memos, pending, duplications, lags, etc.

**Veneer** – Serves detritus-processed data over Plaid-compatible endpoints.

## Development

### Protobuf code generation (bedrock events)

This project uses [betterproto](https://github.com/betterproto/betterproto) for Python code generation from `.proto` files.

**Requirements:**
- [protoc](https://github.com/protocolbuffers/protobuf) (Protocol Buffers compiler)
  - On macOS: `brew install protobuf`
  - On Linux: `sudo apt-get install protobuf-compiler`
  - On Windows: [Download from releases](https://github.com/protocolbuffers/protobuf/releases)

**To regenerate Python code from .proto files:**

```bash
uv run buildproto
```

This will generate Python files in `src/doppelbank/bedrock/generated/` using the `protoc-gen-python_betterproto` plugin from your uv environment.

### Linting, formatting, and type checking

- **Check only (no changes):**
  ```bash
  uv run check
  ```
- **Autofix (apply formatting and autofixable lint):**
  ```bash
  uv run fix
  ```

### Testing

The project includes comprehensive unit tests for all components:

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests for a specific module
uv run pytest tests/test_bedrock_models.py

# Run tests with coverage
uv run pytest --cov=doppelbank
```

### Dependencies

- All Python dependencies (including dev tools) are managed with [uv](https://github.com/astral-sh/uv).
- The only non-Python dependency is `protoc` (see above).

### Bedrock CLI

The Bedrock component provides a CLI for generating synthetic financial events:

```bash
# Generate events in JSON format (default)
uv run python -m doppelbank.bedrock.cli generate --user-id 42 --months 12 --seed 42

# Generate events in binary protobuf format
uv run python -m doppelbank.bedrock.cli generate --user-id 42 --months 3 --format binary --output events.bin

# Validate an event file
uv run python -m doppelbank.bedrock.cli validate events.json
```

## Detritus CLI

Generate Plaid-style sync data from bedrock events:

```sh
uv run detritus -- --input path/to/bedrock.json --output path/to/detritus.json --format json
```

- `--input`: Path to a bedrock events file (json or binary)
- `--output`: Path to output detritus sync file (json or binary)
- `--format`: Output format (`json` or `binary`, default: `json`)

This will read the bedrock events, transform them, and write a Plaid-style sync file.
