"""
Shared protobuf compilation utilities for buildproto and preflight scripts.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

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

PROTO_DIR = Path("protos")
GEN_DIR = Path("src/generated")


def get_proto_files() -> list[Path]:
    """Get list of proto files to compile. Raises error if any are missing."""
    proto_files = []
    for config in PROTO_CONFIGS:
        proto_file = config["proto_file"]
        if not proto_file.exists():
            raise FileNotFoundError(f"Proto file not found: {proto_file}")
        proto_files.append(proto_file)
    return proto_files


def compile_proto_to_directory(proto_file: Path, output_dir: Path) -> None:
    """Compile a single proto file to the specified output directory."""
    subprocess.run(
        [
            "protoc",
            f"--python_betterproto_out={output_dir}",
            "--proto_path=protos",
            str(proto_file),
        ],
        check=True,
    )


def compile_proto_directly(proto_file: Path, final_output_file: Path) -> None:
    """Compile proto to temp directory then move to final location (avoids clobbering)."""
    # Ensure the output directory exists
    output_dir = final_output_file.parent
    output_dir.mkdir(exist_ok=True, parents=True)

    # Use a temp directory to avoid clobbering existing files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Generate to temp directory
        compile_proto_to_directory(proto_file, temp_path)

        # The proto file will generate as {proto_stem}.py in the temp directory
        generated_file = temp_path / f"{proto_file.stem}.py"

        # Verify the expected file was generated
        if not generated_file.exists():
            raise FileNotFoundError(
                f"Expected generated file not created: {generated_file}"
            )

        # Move from temp to final location
        shutil.move(str(generated_file), str(final_output_file))


def ensure_output_directory() -> None:
    """Ensure the output directory exists."""
    GEN_DIR.mkdir(exist_ok=True, parents=True)
