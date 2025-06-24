#!/usr/bin/env python3
"""
Preflight script: checks if buildproto is needed (by generating to a temp dir and comparing), runs check, then tests.
No side effects: fails if codegen is needed, but does not overwrite files.
"""
import subprocess
from pathlib import Path
import sys
import tempfile
import filecmp

PROTO_DIR = Path("src/doppelbank/bedrock")
GEN_DIR = PROTO_DIR / "generated"


def compare_generated(temp_dir, gen_dir):
    dcmp = filecmp.dircmp(temp_dir, gen_dir)
    if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
        return False
    # Recursively check subdirs
    for sub_dcmp in dcmp.subdirs.values():
        if not compare_generated(sub_dcmp.left, sub_dcmp.right):
            return False
    return True


def main():
    proto_files = list(PROTO_DIR.glob("*.proto"))
    if not proto_files:
        print("[!] No .proto files found.")
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Generate code to temp dir
        for proto_file in proto_files:
            subprocess.run(
                [
                    "protoc",
                    f"--python_betterproto_out={tmpdir_path}",
                    f"--proto_path={PROTO_DIR}",
                    str(proto_file),
                ],
                check=True,
            )
        # Compare temp dir to checked-in generated dir
        if not compare_generated(tmpdir_path, GEN_DIR):
            print(
                "[!] You need to run 'uv run buildproto' (generated code is out of date)"
            )
            sys.exit(1)
    print("[✓] Protobuf code is up to date.")
    print("[•] Running code quality checks...")
    result = subprocess.run(["uv", "run", "check"])
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("[•] Running tests...")
    result = subprocess.run(["uv", "run", "pytest"])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
