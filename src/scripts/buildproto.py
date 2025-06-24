#!/usr/bin/env python3
"""
Script to compile all .proto files in bedrock to the generated directory.
"""

# Standard library
import subprocess
import sys
from pathlib import Path


def main():
    proto_dir = Path("src/doppelbank/bedrock")
    out_dir = proto_dir / "generated"
    out_dir.mkdir(exist_ok=True)
    proto_files = list(proto_dir.glob("*.proto"))
    if not proto_files:
        print("No .proto files found.")
        return
    for proto_file in proto_files:
        print(f"Compiling {proto_file}...")
        subprocess.run([
            sys.executable, "-m", "grpc_tools.protoc",
            f"--python_out={out_dir}",
            f"--proto_path={proto_dir}",
            str(proto_file)
        ], check=True)
    print(f"✓ Compiled {len(proto_files)} proto file(s) to {out_dir}")


if __name__ == "__main__":
    main() 