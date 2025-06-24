# Doppel Bank

*“Spin up financial doppelgängers and pull their ledgers through a Plaid-compatible API.”*

Doppel Bank is a developer sandbox that lets you test budgeting, cash-flow, and PFM ideas **without touching real money or PII**.

---

## Quick start (90 seconds)

```
git clone https://github.com/GregorStocks/doppelbank.git
cd doppelbank
uv sync --extra dev

# 1. Generate a new synthetic user (24 months, deterministic seed)
uv run python -m doppelbank.simulator.cli --seed 42 --months 24 > personas/user_0042.json

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
