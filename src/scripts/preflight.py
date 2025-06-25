#!/usr/bin/env python3
"""
Preflight script: checks if buildproto is needed (by generating to a temp dir and comparing),
runs check, then tests.
No side effects: fails if codegen is needed, but does not overwrite files.
"""
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.proto_common import GEN_DIR, compile_proto_to_directory, get_proto_files


def compare_generated(temp_dir: Path | str, gen_dir: Path | str) -> bool:
    dcmp = filecmp.dircmp(temp_dir, gen_dir)
    if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
        return False
    # Recursively check subdirs
    for sub_dcmp in dcmp.subdirs.values():
        if not compare_generated(sub_dcmp.left, sub_dcmp.right):
            return False
    return True


def main() -> None:
    try:
        proto_files = get_proto_files()
    except FileNotFoundError as e:
        print(f"[!] {e}")
        sys.exit(1)

    if not proto_files:
        print("[!] No .proto files configured.")
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Generate code to temp dir using shared logic
        for proto_file in proto_files:
            compile_proto_to_directory(proto_file, tmpdir_path)
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
