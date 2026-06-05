from __future__ import annotations

import io
import logging
import os
from pathlib import Path
import pytest
import yaml

import translator
import machine
import isa

GOLDEN_DIR = Path(__file__).parent / "golden"
UPDATE_GOLDENS = os.environ.get("UPDATE_GOLDENS", "0") == "1"

def str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def parse_interrupt_schedule(input_path: Path | None) -> list[tuple[int, str]]:
    interrupt_schedule: list[tuple[int, str]] = []
    if not input_path or not input_path.exists():
        return interrupt_schedule

    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            tick_val = int(parts[0].strip())
            char = parts[1].strip()
            if len(char) > 1 and char.startswith('"') and char.endswith('"'):
                char = char[1:-1]
            decoded = []
            i = 0
            while i < len(char):
                if char[i] == "\\" and i + 1 < len(char):
                    esc = char[i + 1]
                    if esc == "n":
                        decoded.append("\n")
                    elif esc == "t":
                        decoded.append("\t")
                    elif esc == "0":
                        decoded.append("\x00")
                    elif esc == "\\":
                        decoded.append("\\")
                    else:
                        decoded.append(char[i])
                        i += 1
                        continue
                    i += 2
                else:
                    decoded.append(char[i])
                    i += 1
            char = "".join(decoded)
            interrupt_schedule.append((tick_val, char))
    return interrupt_schedule


@pytest.mark.parametrize(
    "golden_file",
    sorted(GOLDEN_DIR.glob("*.yml")),
    ids=lambda p: p.stem,
)
def test_golden(golden_file: Path) -> None:
    with open(golden_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    source_file = Path(config["in"]["source"])
    input_file = Path(config["in"]["input"]) if config["in"].get("input") else None

    assert source_file.exists(), f"Source file {source_file} not found"
    with open(source_file, encoding="utf-8") as f:
        source_code = f.read()

    code, data = translator.translate(source_code)
    actual_code_hex = isa.to_hex(code)

    interrupt_schedule = parse_interrupt_schedule(input_file)
    memory_size = config.get("config", {}).get("memory_size", 1024)
    limit = config.get("config", {}).get("limit", 10000)

    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    old_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(log_handler)

    try:
        actual_stdout, actual_ticks = machine.simulation(
            code=code,
            data=data,
            interrupt_schedule=interrupt_schedule,
            data_memory_size=memory_size,
            limit=limit,
        )
    finally:
        root_logger.removeHandler(log_handler)
        root_logger.setLevel(old_level)

    actual_journal = log_stream.getvalue()

    actual_code_hex = actual_code_hex.replace("\r\n", "\n").strip()
    actual_stdout = actual_stdout.replace("\r\n", "\n")
    actual_journal = actual_journal.replace("\r\n", "\n").strip()

    expected_code = config.get("out_code", "").replace("\r\n", "\n").strip()
    expected_stdout = config.get("out_stdout", config.get("out", "")).replace("\r\n", "\n")
    expected_journal = config.get("out_journal", "").replace("\r\n", "\n").strip()
    expected_ticks = config.get("ticks", 0)

    if UPDATE_GOLDENS:
        ordered_config = {
            "in": config.get("in", {}),
        }

        if "config" in config:
            ordered_config["config"] = config["config"]

        ordered_config["ticks"] = actual_ticks
        ordered_config["out_stdout"] = actual_stdout
        ordered_config["out_code"] = actual_code_hex
        ordered_config["out_journal"] = actual_journal

        with open(golden_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(ordered_config, f, allow_unicode=True, sort_keys=False, width=1000)
    else:
        assert actual_code_hex == expected_code, f"Machine code mismatch in {golden_file.name}"
        assert actual_stdout == expected_stdout, f"Stdout mismatch in {golden_file.name}"
        assert actual_journal == expected_journal, f"Simulation journal mismatch in {golden_file.name}"
        assert actual_ticks == expected_ticks, f"Ticks mismatch in {golden_file.name}"