"""Golden tests for assembler and machine simulation."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

GOLDEN_DIR = Path(__file__).parent / "golden"


def run_test(source: str, input_file: str | None = None) -> tuple[str, int]:
    """Translate and run a program, returning (output, ticks)."""
    source_path = Path(source)
    out_bin = Path("out") / source_path.with_suffix(".bin").name
    out_bin.parent.mkdir(exist_ok=True)

    # Translate
    subprocess.run(
        ["python", "translator.py", str(source_path), str(out_bin)],
        check=True,
        capture_output=True,
        text=True,
    )

    # Run machine
    cmd = ["python", "machine.py", str(out_bin)]
    if input_file:
        cmd.append(str(input_file))
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = result.stdout.splitlines()
    # Last line is "ticks: N", everything before is program output
    if len(lines) >= 2 and lines[-1].startswith("ticks:"):
        output_lines = lines[:-1]
        ticks_line = lines[-1]
    else:
        output_lines = lines
        ticks_line = "ticks: 0"
    output = "\n".join(output_lines)
    if output and not output.endswith("\n"):
        output += "\n"
    ticks = int(ticks_line.replace("ticks:", "").strip())
    return output, ticks


@pytest.mark.parametrize(
    "golden_file",
    sorted(GOLDEN_DIR.glob("*.yml")),
    ids=lambda p: p.stem,
)
def test_golden(golden_file: Path) -> None:
    """Run golden test from YAML config."""
    config = yaml.safe_load(golden_file.read_text(encoding="utf-8"))
    source = config["in"]["source"]
    input_file = config["in"].get("input")
    expected_out = config["out"]
    expected_ticks = config.get("ticks", 0)

    actual_out, actual_ticks = run_test(source, input_file)

    assert actual_out == expected_out, f"Output mismatch for {golden_file.stem}"
    assert actual_ticks == expected_ticks, f"Tick mismatch for {golden_file.stem}: {actual_ticks} != {expected_ticks}"
