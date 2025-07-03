#!/usr/bin/env python3
"""
Preflight script: runs code quality checks and tests.
"""

import subprocess
import sys


def main() -> None:
    print("[•] Running code quality fixes...")
    result = subprocess.run(["uv", "run", "fix"])
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("[•] Running tests...")
    result = subprocess.run(["uv", "run", "pytest"])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
