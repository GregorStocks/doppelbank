import json
import subprocess
from pathlib import Path

def test_detritus_cli(tmp_path):
    bedrock_path = tmp_path / "bedrock.json"
    detritus_path = tmp_path / "detritus.json"
    # Generate bedrock events
    subprocess.run([
        "uv", "run", "python", "-m", "doppelbank.bedrock.cli", "generate",
        "--user-id", "testuser", "--output", str(bedrock_path), "--format", "json", "--seed", "42"
    ], check=True)
    # Run detritus CLI
    subprocess.run([
        "uv", "run", "python", "-m", "doppelbank.detritus.cli",
        "--input", str(bedrock_path), "--output", str(detritus_path), "--format", "json"
    ], check=True)
    # Check output
    assert detritus_path.exists()
    with open(detritus_path) as f:
        data = json.load(f)
    assert "added" in data
    assert isinstance(data["added"], list)
    assert len(data["added"]) > 0 