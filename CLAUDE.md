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