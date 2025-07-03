# Doppel Bank

*"Spin up financial doppelgängers and pull their ledgers through a Plaid-compatible API."*

Doppel Bank is a developer sandbox that lets you test budgeting, cash-flow, and PFM ideas **without touching real money or PII**.

---

## Quick start (90 seconds)

```
git clone https://github.com/GregorStocks/doppelbank.git
cd doppelbank
uv sync --extra dev

# 1. Generate a new synthetic user (24 months)
uv run persona_generator generate --user-id 0042 --months 24 > personas/user_0042.json

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

### Persona Generator CLI

The Persona Generator component provides a CLI for generating synthetic financial events:

```bash
# Generate events in JSON format
uv run persona_generator --months 12
```