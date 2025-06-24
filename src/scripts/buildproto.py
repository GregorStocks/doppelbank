#!/usr/bin/env python3
"""
Script to compile protos/bedrock.proto and protos/detritus.proto to src/generated/bedrock.py and src/generated/detritus.py using protoc and the betterproto plugin.
Requires: protoc (brew install protobuf)
"""
import subprocess
from pathlib import Path
import shutil

PROTO_CONFIGS = [
    {
        "proto_file": Path("protos/bedrock.proto"),
        "out_file": Path("src/generated/bedrock.py"),
    },
    {
        "proto_file": Path("protos/detritus.proto"),
        "out_file": Path("src/generated/detritus.py"),
    },
]

def main():
    Path("src/generated").mkdir(exist_ok=True, parents=True)
    for config in PROTO_CONFIGS:
        proto_file = config["proto_file"]
        out_file = config["out_file"]
        if not proto_file.exists():
            continue
        print(f"Compiling {proto_file} to {out_file} with protoc + betterproto plugin...")
        subprocess.run([
            "protoc",
            f"--python_betterproto_out=src/generated",
            f"--proto_path=protos",
            str(proto_file)
        ], check=True)
        # The generated file will be named after the proto file (e.g., bedrock.py)
        generated_file = Path("src/generated") / proto_file.stem / f"{proto_file.stem}.py"
        if generated_file.exists():
            shutil.move(str(generated_file), str(out_file))
            # Remove the now-empty directory
            try:
                (Path("src/generated") / proto_file.stem).rmdir()
            except Exception:
                pass
        print(f"✓ Compiled {proto_file} to {out_file}")

if __name__ == "__main__":
    main()
