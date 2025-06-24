#!/usr/bin/env python3
import sys
import subprocess

CHECK_COMMANDS = [
    ["uv", "run", "ruff", "check", "src/", "tests/"],
    ["uv", "run", "black", "--check", "src/", "tests/"],
    ["uv", "run", "mypy", "src/doppelbank/bedrock/", "--ignore-missing-imports"],
]

FIX_COMMANDS = [
    ["uv", "run", "ruff", "check", "--fix", "src/", "tests/"],
    ["uv", "run", "black", "src/", "tests/"],
]

def run_commands(commands):
    for cmd in commands:
        print(f"\n$ {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            sys.exit(result.returncode)

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"check", "fix"}:
        print("Usage: uv run python src/scripts/lint.py [check|fix]")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "check":
        run_commands(CHECK_COMMANDS)
    elif mode == "fix":
        run_commands(FIX_COMMANDS)

if __name__ == "__main__":
    main() 