from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field

from isa import (
    MNEMONIC_TO_OPCODE_MODE,
    Mode,
    Opcode,
    Term,
    to_bytes,
    to_hex,
)


@dataclass
class ParserState:
    section: str = ".text"
    data_addr: int = 0
    code_addr: int = 0
    labels: dict[str, tuple[str, int]] = field(default_factory=dict)
    constants: dict[str, int] = field(default_factory=dict)
    data: list[tuple[int, int | str]] = field(default_factory=list)
    code: list[dict] = field(default_factory=list)


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def parse_number(token: str) -> int:
    token = token.strip()
    if token.startswith("0x") or token.startswith("0X"):
        return int(token, 16)
    return int(token)


def parse_operand(token: str, state: ParserState) -> tuple[Mode, int | str]:
    token = token.strip()
    if token.startswith("#"):
        inner = token[1:].strip()
        try:
            return Mode.IMMEDIATE, parse_number(inner)
        except ValueError:
            return Mode.IMMEDIATE, inner  # label or constant
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return Mode.INDIRECT, inner
    if token.startswith("@"):
        inner = token[1:].strip()
        return Mode.RELATIVE, inner
    try:
        return Mode.ABSOLUTE, parse_number(token)
    except ValueError:
        return Mode.ABSOLUTE, token


def first_pass(text: str) -> ParserState:
    state = ParserState()
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = strip_comment(raw_line)
        if not line:
            continue

        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            label, rest = line.split(":", 1)
            label = label.strip()
            if state.section == ".data":
                state.labels[label] = (".data", state.data_addr)
            else:
                state.labels[label] = (".text", state.code_addr)
            line = rest.strip()

        if line.startswith("."):
            parts = line.split(None, 1)
            directive = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ""

            if directive == ".section":
                state.section = rest.strip().lower()
            elif directive == ".org":
                addr = parse_number(rest.strip())
                if state.section == ".data":
                    state.data_addr = addr
                else:
                    state.code_addr = addr
            elif directive == ".equ":
                tokens = rest.split(None, 1)
                name = tokens[0]
                value = parse_number(tokens[1])
                state.constants[name] = value
            elif directive == ".string":
                match = re.match(r'"(.*)"', rest)
                if not match:
                    raise ValueError(f"Invalid .string: {rest}")
                string = match.group(1)
                decoded = []
                i = 0
                while i < len(string):
                    if string[i] == "\\" and i + 1 < len(string):
                        esc = string[i + 1]
                        if esc == "n":
                            decoded.append("\n")
                        elif esc == "t":
                            decoded.append("\t")
                        elif esc == "\\":
                            decoded.append("\\")
                        elif esc == '"':
                            decoded.append('"')
                        else:
                            decoded.append(string[i])
                            i += 1
                            continue
                        i += 2
                    else:
                        decoded.append(string[i])
                        i += 1
                addr = state.data_addr
                for ch in decoded:
                    state.data.append((addr, ord(ch)))
                    addr += 1
                state.data.append((addr, 0))
                addr += 1
                state.data_addr = addr
            elif directive == ".word":
                for token in rest.split(","):
                    token = token.strip()
                    try:
                        val: int | str = parse_number(token)
                    except ValueError:
                        val = token
                    state.data.append((state.data_addr, val))
                    state.data_addr += 1
            continue

        if not line:
            continue

        if state.section != ".text":
            raise ValueError(f"Instruction in data section at line {line_no}: {line}")

        tokens = line.split(None, 1)
        mnemonic = tokens[0].lower()
        operand_str = tokens[1] if len(tokens) > 1 else ""

        opcode, mode_override = MNEMONIC_TO_OPCODE_MODE[mnemonic]

        if opcode in (Opcode.HALT, Opcode.RET, Opcode.NOT):
            state.code.append(
                {
                    "index": state.code_addr,
                    "opcode": opcode,
                    "mode": Mode.ABSOLUTE,
                    "term": Term(line_no, 0, line),
                }
            )
            state.code_addr += 1
        elif opcode == Opcode.SPECIAL:
            assert mode_override is not None
            if mode_override in (Mode.JC, Mode.JNC):
                mode, arg = parse_operand(operand_str, state)
                state.code.append(
                    {
                        "index": state.code_addr,
                        "opcode": opcode,
                        "mode": mode_override,
                        "arg": arg,
                        "term": Term(line_no, 0, line),
                    }
                )
            else:
                state.code.append(
                    {
                        "index": state.code_addr,
                        "opcode": opcode,
                        "mode": mode_override,
                        "term": Term(line_no, 0, line),
                    }
                )
            state.code_addr += 1
        else:
            mode, arg = parse_operand(operand_str, state)
            if mode_override is not None:
                mode = mode_override
            state.code.append(
                {
                    "index": state.code_addr,
                    "opcode": opcode,
                    "mode": mode,
                    "arg": arg,
                    "term": Term(line_no, 0, line),
                }
            )
            state.code_addr += 1

    return state


def resolve_value(val: int | str, state: ParserState, current_addr: int = 0) -> int:
    if isinstance(val, int):
        return val
    if val in state.constants:
        return state.constants[val]
    if val in state.labels:
        section, addr = state.labels[val]
        if section == ".text":
            return addr
        return addr
    raise ValueError(f"Undefined symbol: {val}")


def second_pass(state: ParserState) -> tuple[list[dict], list[tuple[int, int]]]:
    resolved_data: list[tuple[int, int]] = []
    for addr, val in state.data:
        if isinstance(val, str):
            val = resolve_value(val, state)
        resolved_data.append((addr, val))

    resolved_code: list[dict] = []
    for instr in state.code:
        new_instr = dict(instr)
        if "arg" in new_instr:
            arg = new_instr["arg"]
            if isinstance(arg, str):
                arg = resolve_value(arg, state, new_instr["index"])
            if new_instr["mode"] == Mode.RELATIVE:
                arg = arg - (new_instr["index"] + 1)
            new_instr["arg"] = arg & 0xFFFFFF
        resolved_code.append(new_instr)

    return resolved_code, resolved_data


def pad_code(code: list[dict]) -> list[dict]:
    if not code:
        return code
    max_index = max(instr["index"] for instr in code)
    code_dict = {instr["index"]: instr for instr in code}
    padded: list[dict] = []
    for i in range(max_index + 1):
        if i in code_dict:
            padded.append(code_dict[i])
        else:
            padded.append({"index": i, "opcode": Opcode.HALT, "mode": Mode.ABSOLUTE})
    return padded


def translate(text: str) -> tuple[list[dict], list[tuple[int, int]]]:
    state = first_pass(text)
    code, data = second_pass(state)
    data.sort(key=lambda x: x[0])
    code.sort(key=lambda x: x["index"])
    code = pad_code(code)
    return code, data


def main(source: str, target: str) -> None:
    with open(source, encoding="utf-8") as f:
        text = f.read()

    code, data = translate(text)
    binary_code = to_bytes(code)
    hex_code = to_hex(code)

    os.makedirs(os.path.dirname(os.path.abspath(target)) or ".", exist_ok=True)
    with open(target, "wb") as f:
        f.write(binary_code)
    with open(target + ".hex", "w", encoding="utf-8") as f:
        f.write(hex_code)

    import json

    with open(target + ".data.json", "w", encoding="utf-8") as f:
        json.dump({"data": data}, f)

    print(f"source LoC: {len(text.splitlines())} code instr: {len(code)} data words: {len(data)}")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Usage: translator.py <source.asm> <target.bin>"
    _, source, target = sys.argv
    main(source, target)
