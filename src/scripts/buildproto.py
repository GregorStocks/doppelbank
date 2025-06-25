#!/usr/bin/env python3
"""
Script to compile protos/bedrock.proto and protos/detritus.proto to src/generated/bedrock.py
and src/generated/detritus.py using protoc and the betterproto plugin.
Requires: protoc (brew install protobuf)
"""
from scripts.proto_common import PROTO_CONFIGS, compile_proto_directly


def main() -> None:
    for config in PROTO_CONFIGS:
        proto_file = config["proto_file"]
        out_file = config["out_file"]

        if not proto_file.exists():
            print(f"[!] Proto file not found: {proto_file}")
            continue

        print(
            f"Compiling {proto_file} to {out_file} with protoc + betterproto plugin..."
        )
        compile_proto_directly(proto_file, out_file)
        print(f"✓ Compiled {proto_file} to {out_file}")


if __name__ == "__main__":
    main()
