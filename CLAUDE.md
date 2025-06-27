Please refer to docs/coding-standards.md for general coding standards.

Check lint: `uv run check`

Autofix: `uv run fix`

Run `uv run preflight` after every change. This runs all our linters and tests.

When adding new functionality, start by writing a test that will fail (red), then implement the code to make it pass (green).

Leave explicit TODOs in the code when you're leaving something unfinished.

Never ignore type/lint errors (e.g. with noqa) - always actually fix them.

## TODOs / Unfinished Work
- [ ] **Veneer**
    - Support the exact same request/response format as the Plaid API (though likely with additional parameters and metadata, and perhaps missing some params and fields)
    - Support for timestamps in the query ("tell me what the transactions would have looked like yesterday")
    - Error handling.
    - Documentation for everything different from Plaid.
    - Support for other endpoints, such that a regular Plaid client could talk to Veneer and not get too confused.
    - Fully support the data model in the Detritus protobuf.
- [ ] **Detritus**
    - Support more strangeness (duplicate transactions, merchant/memo problems, etc etc etc)
- [ ] **Bedrock**
    - Better user-psychology modeling
    - Pull stuff out of cli.py
- [ ] **General**
    - Clean up CLAUDE.md and move the stuff that isn't Claude-specific to more general developer documentation
    - Github commit hooks?
    - Clean up protobuf docstrings (ensure we don't have so much duplication around amounts/timestamps/etc)
