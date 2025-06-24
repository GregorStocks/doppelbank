# Keep this file up to date as you do stuff.

## Current State
- Barebones MVP probably works end-to-end, from "generating a fake user" through to "serving up their data via Plaid API".
- Probably ~100% test coverage.

## TODOs / Unfinished Work
- [ ] **Veneer**
    - Support the exact same request/response format as the Plaid API (though likely with additional parameters and metadata, and perhaps missing some params and fields)
    - Support for timestamps in the query ("tell me what the transactions would have looked like yesterday")
    - Error handling.
    - Documentation for everything different from Plaid.
    - Support for other endpoints, such that a regular Plaid client could talk to Veneer and not get too confused.
    - Fully support the data model in the Detritus protobuf.
- [ ] **Detritus**
    - Add CSV support
    - Implement RemovePending and UpdateBalance BankEvent types in transformation logic.
    - Add validation for Bedrock events (don't just skip events with missing fields).
    - Fully support the data model in the Bedrock protobuf.
    - Support more strangeness (duplicate transactions, merchant/memo problems, etc etc etc)
- [ ] **Bedrock**
    - Better user-psychology modeling
    - Pull stuff out of cli.py
    - Clean up serde.py mess (why are there two of them?)
    - Clean up protobuf docstrings (ensure we don't have so much duplication around amounts/timestamps/etc)
- [ ] **General**
    - Clean up CLAUDE.md and move the stuff that isn't Claude-specific to more general developer documentation
    - Github commit hooks?

# Claude Coding Standards

## Import Rules

1. **Always use absolute imports** - Use `from doppelbank.bedrock.models import ...` instead of relative imports like `from .models import ...`

2. **All imports at the top** - Never scatter imports throughout the file. Group them logically at the top:
   - Standard library imports first
   - Third-party imports second  
   - Local project imports last
   - Each group separated by a blank line

## Tooling and Workflow

- **All Python dependencies** (including dev tools and codegen plugins) are managed with [uv](https://github.com/astral-sh/uv).
- **All project scripts** (lint, fix, buildproto, preflight, etc.) live in `src/scripts/` and are exposed as uv project scripts in `pyproject.toml`.
- **No global Python tools** are required. The only non-Python dependency is `protoc` (the Protocol Buffers compiler).
- **Protobuf codegen** uses `protoc` with the `protoc-gen-python_betterproto` plugin from the uv environment. To regenerate code: `uv run buildproto`
- **Linting, formatting, and type checking** are unified and ergonomic:
  - Check only: `uv run check`
  - Autofix: `uv run fix`
- **Testing**: `uv run pytest`
- **Preflight:**
  - Run `uv run preflight` after every agent run or before committing code. This will:
    - Generate Python code from `.proto` files to a temporary directory
    - Compare the temp-generated files to the checked-in generated files
    - Fail (with no side effects) if any differences are found, instructing you to run `uv run buildproto`
    - Run all code quality checks and tests if everything is up to date

## Protoc Requirement
- You must have `protoc` installed on your system (e.g., `brew install protobuf` on macOS).
- The Python-side plugin (`protoc-gen-python_betterproto`) is managed by uv and does not require global installation.

## Scripts and Entrypoints
- All scripts are written in Python (no bash) and live in `src/scripts/`.
- Scripts are exposed as uv project scripts in `pyproject.toml` for ergonomic usage:
  - `uv run check`, `uv run fix`, `uv run buildproto`, `uv run preflight`, etc.

## Directory Structure
- All source code is under `src/`.
- All scripts are under `src/scripts/` and are Python packages (with `__init__.py`).

## General Best Practices
- Keep the developer workflow as simple as possible: clone, `uv sync --extra dev`, and use the provided uv scripts.
- Prefer Python scripts over bash for all automation.

## Test-Driven Development (TDD) Practice
- **Always write tests that fail first.**
    - When adding new functionality, start by writing a test that will fail (red), then implement the code to make it pass (green).
    - This ensures your tests are meaningful and actually test the new code.
- **Confirm new tests are being run:**
    - When adding a new test file or test case, temporarily add `assert False` or a `print()` statement in the test to verify it is picked up by pytest.
    - Run `uv run python -m pytest -v` and confirm you see the failure or output.
    - Remove the temporary assertion or print after confirming.
- This practice helps prevent false positives and ensures your test suite is always up to date and effective.

## TODOs and Developer Hygiene

Leave explicit TODOs in the code when you're leaving something unfinished.