#!/usr/bin/env python3
import subprocess
import sys

CHECK_COMMANDS = [
    ["uv", "run", "ruff", "format", "--check", "src/", "tests/"],
    ["uv", "run", "ruff", "check", "src/", "tests/"],
    ["uv", "run", "mypy", "src/", "tests/"],
]

FIX_COMMANDS = [
    ["uv", "run", "ruff", "format", "src/", "tests/"],
    ["uv", "run", "ruff", "check", "--fix", "src/", "tests/"],
]


def run_commands(commands: list[list[str]]) -> None:
    for cmd in commands:
        print(f"\n$ {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            sys.exit(result.returncode)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"check", "fix"}:
        print("Usage: uv run python src/scripts/lint.py [check|fix]")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "check":
        run_commands(CHECK_COMMANDS)
    elif mode == "fix":
        run_commands(FIX_COMMANDS)


def check() -> None:
    """Entry point for uv run check"""
    run_commands(CHECK_COMMANDS)


def fix() -> None:
    """Entry point for uv run fix"""
    run_commands(FIX_COMMANDS)


if __name__ == "__main__":
    main()
