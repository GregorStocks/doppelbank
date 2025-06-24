#!/usr/bin/env python3
"""
Script to compile all .proto files in bedrock to the generated directory using protoc and the betterproto plugin.
Requires: protoc (brew install protobuf)
"""
import subprocess
from pathlib import Path
import hashlib

PROTO_DIR = Path("src/doppelbank/bedrock")
GEN_DIR = PROTO_DIR / "generated"


def hash_files(files):
    h = hashlib.sha256()
    for f in sorted(files, key=lambda x: str(x)):
        with open(f, "rb") as fp:
            h.update(fp.read())
    return h.hexdigest()


def main():
    proto_files = list(PROTO_DIR.glob("*.proto"))
    out_dir = GEN_DIR
    out_dir.mkdir(exist_ok=True)
    if not proto_files:
        print("No .proto files found.")
        return
    for proto_file in proto_files:
        print(f"Compiling {proto_file} with protoc + betterproto plugin...")
        subprocess.run([
            "protoc",
            f"--python_betterproto_out={out_dir}",
            f"--proto_path={PROTO_DIR}",
            str(proto_file)
        ], check=True)
    # Write proto hash for preflight check
    proto_hash = hash_files(proto_files)
    hash_file = out_dir / ".proto_hash"
    with open(hash_file, "w") as f:
        f.write(proto_hash)
    print(f"✓ Compiled {len(proto_files)} proto file(s) to {out_dir}")
    print(f"✓ Wrote proto hash to {hash_file}")


if __name__ == "__main__":
    main()
