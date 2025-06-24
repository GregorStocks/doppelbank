#!/usr/bin/env python3
"""
Script to compile all .proto files in protos/bedrock and protos/detritus to their generated directories in src/ using protoc and the betterproto plugin.
Requires: protoc (brew install protobuf)
"""
import subprocess
from pathlib import Path
import hashlib

PROTO_CONFIGS = [
    {
        "proto_dir": Path("protos/bedrock"),
        "out_dir": Path("src/doppelbank/bedrock/generated"),
        "hash_for_preflight": True,
    },
    {
        "proto_dir": Path("protos/detritus"),
        "out_dir": Path("src/doppelbank/detritus/generated"),
        "hash_for_preflight": False,
    },
]


def hash_files(files):
    h = hashlib.sha256()
    for f in sorted(files, key=lambda x: str(x)):
        with open(f, "rb") as fp:
            h.update(fp.read())
    return h.hexdigest()


def main():
    for config in PROTO_CONFIGS:
        proto_dir = config["proto_dir"]
        out_dir = config["out_dir"]
        out_dir.mkdir(exist_ok=True, parents=True)
        proto_files = list(proto_dir.glob("*.proto"))
        if not proto_files:
            continue
        for proto_file in proto_files:
            print(f"Compiling {proto_file} with protoc + betterproto plugin...")
            subprocess.run([
                "protoc",
                f"--python_betterproto_out={out_dir}",
                f"--proto_path={proto_dir}",
                str(proto_file)
            ], check=True)
        # Write proto hash for preflight check (bedrock only)
        if config["hash_for_preflight"]:
            proto_hash = hash_files(proto_files)
            hash_file = out_dir / ".proto_hash"
            with open(hash_file, "w") as f:
                f.write(proto_hash)
        print(f"✓ Compiled {len(proto_files)} proto file(s) to {out_dir}")


if __name__ == "__main__":
    main()
