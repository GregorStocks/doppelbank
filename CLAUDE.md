# Keep this file up to date as you do stuff.

## Current State
- Barebones MVP probably works end-to-end, from "generating a fake user" through to "serving up their data via Plaid API".
- Probably ~100% test coverage.

## TODOs / Unfinished Work
- [ ] **Veneer**
    - Serve in exactly the same API format as Plaid.
    - Support for timestamps in the query ("tell me what the transactions would have looked like yesterday")
    - Better tests:
      - Actually stand up a full server and query it via curl, to ensure our coverage is truly end-to-end
      - Single test that goes from Bedrock to Veneer
    - Use account_id (not filename) to select ledger file; map account_id to file internally.
    - Remove 'format' and 'file' params from API.
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

# Claude Coding Standards

## Import Rules

1. **Always use absolute imports** - Use `from doppelbank.bedrock.models import ...` instead of relative imports like `from .models import ...`

2. **All imports at the top** - Never scatter imports throughout the file. Group them logically at the top:
   - Standard library imports first
   - Third-party imports second  
   - Local project imports last
   - Each group separated by a blank line

## Example

```python
# Standard library
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
from google.protobuf import text_format
from google.protobuf.json_format import MessageToJson

# Local project
from doppelbank.bedrock.models import create_paycheck_event, save_events
from doppelbank.bedrock.generated import events_pb2
```

## Why These Rules?

- **Absolute imports** are more explicit and work better with IDEs and linters
- **Top-level imports** make code more readable and avoid import-time side effects
- **Consistent structure** makes the codebase easier to navigate and maintain

# Doppelbank Project Conventions and Best Practices

## Tooling and Workflow

- **All Python dependencies** (including dev tools and codegen plugins) are managed with [uv](https://github.com/astral-sh/uv).
- **All project scripts** (lint, fix, buildproto, preflight, etc.) live in `src/scripts/` and are exposed as uv project scripts in `pyproject.toml`.
- **No global Python tools** are required. The only non-Python dependency is `protoc` (the Protocol Buffers compiler).
- **Protobuf codegen** uses `protoc` with the `protoc-gen-python_betterproto` plugin from the uv environment. To regenerate code:
  ```bash
  uv run buildproto
  ```
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

## Ruff Configuration
- **Ruff's defaults are recommended.**
  - No custom `select`, `ignore`, or `line-length` unless you have a strong reason.
  - This keeps the config simple and future-proof.
- If you need to override rules for legacy or special cases, do so minimally in `pyproject.toml`.

## Scripts and Entrypoints
- All scripts are written in Python (no bash) and live in `src/scripts/`.
- Scripts are exposed as uv project scripts in `pyproject.toml` for ergonomic usage:
  - `uv run check`, `uv run fix`, `uv run buildproto`, `uv run preflight`, etc.
- Scripts can also be run as modules (e.g., `uv run -m scripts.lint check`), but the project scripts are preferred for ergonomics.

## Directory Structure
- All source code is under `src/`.
- All scripts are under `src/scripts/` and are Python packages (with `__init__.py`).
- Generated code from `.proto` files goes in `src/doppelbank/bedrock/generated/`.

## General Best Practices
- Keep the developer workflow as simple as possible: clone, `uv sync --extra dev`, and use the provided uv scripts.
- Avoid global Python tools or dependencies outside of `protoc`.
- Prefer Python scripts over bash for all automation.
- Use ruff, black, and mypy for code quality, with unified commands.
- Document any workflow changes in this file and the README.

# Doppelbank Project Conventions (Claude Edition)

## General Principles
- All code is modern Python 3, using dataclasses, type hints, and idiomatic style.
- Protobuf schemas live in `protos/`, generated code in `src/doppelbank/*/generated/`.
- All scripts and CLIs live in `src/scripts/` or as `src/doppelbank/*/cli.py`.
- All serialization is via betterproto, with generic helpers in `lib/serde.py`.
- All developer workflow is via `uv` (https://github.com/astral-sh/uv).

## Running Scripts and CLIs
- **ALWAYS use `uv run` to invoke scripts and CLIs.**
    - Example: `uv run python -m doppelbank.bedrock.cli ...`
    - Example: `uv run python -m doppelbank.detritus.cli ...`
- Do **NOT** use `python` or `python3` directly. This will not set up the environment or PYTHONPATH correctly.
- `uv` automatically sets up `PYTHONPATH=src` so imports work as expected.
- `uv` does **not** support `[tool.uv.scripts]` in `pyproject.toml` (as of 2024-06). Ignore any instructions to use this feature.
- If you want to add ergonomic scripts, use shell aliases or Makefile targets, not `[tool.uv.scripts]`.

## Example CLI Usage

```sh
uv run python -m doppelbank.bedrock.cli generate --user-id testuser --output bedrock.json --format json --seed 42
uv run python -m doppelbank.detritus.cli --input bedrock.json --output detritus.json --format json
```

## Testing and Linting
- Run tests: `uv run python -m pytest`
- Run lint: `uv run python src/scripts/lint.py`
- Run preflight: `uv run python src/scripts/preflight.py`

## Protobuf Codegen
- Run codegen: `uv run python src/scripts/buildproto.py`
- Only `protoc` is required as an external dependency.

## Test-Driven Development (TDD) Practice
- **Always write tests that fail first.**
    - When adding new functionality, start by writing a test that will fail (red), then implement the code to make it pass (green).
    - This ensures your tests are meaningful and actually test the new code.
- **Confirm new tests are being run:**
    - When adding a new test file or test case, temporarily add `assert False` or a `print()` statement in the test to verify it is picked up by pytest.
    - Run `uv run python -m pytest -v` and confirm you see the failure or output.
    - Remove the temporary assertion or print after confirming.
- This practice helps prevent false positives and ensures your test suite is always up to date and effective.

## Summary
- **Never** use `python` or `python3` directly.
- **Always** use `uv run ...` for everything.
- Ignore `[tool.uv.scripts]` in `pyproject.toml`.
- All scripts and CLIs are invoked via `uv run python -m ...`.

## TODOs and Developer Hygiene

Leave explicit TODOs in the code when you're leaving something unfinished.