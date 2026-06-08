from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field

from isa import (
    MNEMONIC_TO_OPCODE_MODE,
    AddressingMode,
    Opcode,
    SpecialOpcode,
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


def parse_operand(token: str) -> tuple[AddressingMode, int | str]:
    token = token.strip()
    if token.startswith("#"):
        inner = token[1:].strip()
        try:
            return AddressingMode.IMMEDIATE, parse_number(inner)
        except ValueError:
            return AddressingMode.IMMEDIATE, inner
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return AddressingMode.INDIRECT, inner
    if token.startswith("@"):
        inner = token[1:].strip()
        return AddressingMode.RELATIVE, inner
    try:
        return AddressingMode.ABSOLUTE, parse_number(token)
    except ValueError:
        return AddressingMode.ABSOLUTE, token


def preprocess(text: str) -> str:
    lines = text.splitlines()
    processed_lines = []

    skip_stack: list[bool] = []
    constants: dict[str, int] = {}

    for line_no, raw_line in enumerate(lines, 1):
        line = strip_comment(raw_line)
        if not line:
            if not skip_stack or not skip_stack[-1]:
                processed_lines.append(raw_line)
            continue

        parts = line.split(None, 2)
        directive = parts[0].lower()

        if directive == ".if":
            if len(parts) < 2:
                raise ValueError(f"Missing condition for .if at line {line_no}")
            cond_var = parts[1]
            val = constants.get(cond_var, 0)
            skip_stack.append(val == 0)
            continue
        if directive == ".else":
            if not skip_stack:
                raise ValueError(f"Orphaned .else at line {line_no}")
            skip_stack[-1] = not skip_stack[-1]
            continue
        if directive == ".endif":
            if not skip_stack:
                raise ValueError(f"Orphaned .endif at line {line_no}")
            skip_stack.pop()
            continue
        if directive == ".equ":
            if not skip_stack or not skip_stack[-1]:
                sub_parts = line.split(None, 2)
                if len(sub_parts) >= 3:
                    name = sub_parts[1]
                    try:
                        val = parse_number(sub_parts[2])
                        constants[name] = val
                    except ValueError:
                        pass
                processed_lines.append(raw_line)
            continue

        if not skip_stack or not skip_stack[-1]:
            processed_lines.append(raw_line)

    lines = processed_lines
    processed_lines = []
    macros = {}
    in_macro = False
    current_macro_name = None
    current_macro_lines: list[str] = []

    for line_no, raw_line in enumerate(lines, 1):
        line = strip_comment(raw_line)
        if not line:
            if not in_macro:
                processed_lines.append(raw_line)
            continue

        parts = line.split(None, 1)
        directive = parts[0].lower()

        if directive == ".macro":
            if in_macro:
                raise ValueError(f"Nested macros are not allowed at line {line_no}")
            if len(parts) < 2:
                raise ValueError(f"Missing macro name at line {line_no}")
            in_macro = True
            current_macro_name = parts[1].strip()
            current_macro_lines = []
            continue
        if directive == ".endmacro":
            if not in_macro:
                raise ValueError(f"Orphaned .endmacro at line {line_no}")
            in_macro = False
            macros[current_macro_name] = current_macro_lines
            continue

        if in_macro:
            current_macro_lines.append(raw_line)
        else:
            line_to_check = line
            label_prefix = ""
            if ":" in line_to_check and not line_to_check.startswith(" ") and not line_to_check.startswith("\t"):
                sub_parts = line_to_check.split(":", 1)
                label_prefix = sub_parts[0].strip() + ":"
                line_to_check = sub_parts[1].strip()

            if line_to_check in macros:
                expanded = list(macros[line_to_check])
                if label_prefix:
                    if expanded:
                        expanded[0] = label_prefix + " " + expanded[0]
                    else:
                        expanded = [label_prefix]
                processed_lines.extend(expanded)
            else:
                processed_lines.append(raw_line)

    return "\n".join(processed_lines)


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

        if opcode == Opcode.NOP:
            state.code.append(
                {
                    "index": state.code_addr,
                    "opcode": opcode,
                    "mode": AddressingMode.ABSOLUTE,
                    "term": Term(line_no, 0, line),
                }
            )
            state.code_addr += 1
        elif opcode == Opcode.SPECIAL:
            assert mode_override is not None
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
            parsed_mode, arg = parse_operand(operand_str)
            mode: AddressingMode | SpecialOpcode = mode_override if mode_override is not None else parsed_mode
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


def resolve_value(val: int | str, state: ParserState) -> int:
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
                arg = resolve_value(arg, state)
            if new_instr["mode"] == AddressingMode.RELATIVE:
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
            padded.append({"index": i, "opcode": Opcode.NOP, "mode": AddressingMode.ABSOLUTE})
    return padded


def translate(text: str) -> tuple[list[dict], list[tuple[int, int]], int]:
    text = preprocess(text)
    state = first_pass(text)
    if "start" not in state.labels:
        raise ValueError("Translation error: Mandatory entry point 'start:' label is missing")

    start_section, start_addr = state.labels["start"]
    if start_section != ".text":
        raise ValueError("Translation error: 'start:' label must be in the .text section")

    code, data = second_pass(state)
    data.sort(key=lambda x: x[0])
    code.sort(key=lambda x: x["index"])
    code = pad_code(code)
    return code, data, start_addr


def main(source: str, target: str) -> None:
    with open(source, encoding="utf-8") as f:
        text = f.read()

    code, data, start_addr = translate(text)
    binary_code = to_bytes(code, start_addr)
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
