from __future__ import annotations

import json
import struct
from collections import namedtuple
from enum import Enum


class Opcode(int, Enum):
    NOP = 0x0
    LOAD = 0x1
    STORE = 0x2
    ADD = 0x3
    SUB = 0x4
    AND = 0x5
    OR = 0x6
    JMP = 0x7
    JZ = 0x8
    JN = 0x9
    JC = 0xA
    JNC = 0xB
    CALL = 0xC
    PUSH = 0xD
    POP = 0xE
    SPECIAL = 0xF


class Mode(int, Enum):
    ABSOLUTE = 0x0
    IMMEDIATE = 0x1
    INDIRECT = 0x2
    RELATIVE = 0x3

    EI = 0x0
    DI = 0x1
    IRET = 0x2
    INC = 0x3
    DEC = 0x4
    NOT = 0x5
    RET = 0x6
    HALT = 0x7


INPUT_PORT = 0xFFFFF0
OUTPUT_PORT = 0xFFFFF1
OUTPUT_NUM_PORT = 0xFFFFF2
IVT_INPUT = 0xFFFFF3
DEFAULT_IVT_INPUT = 0x10

Term = namedtuple("Term", ["line", "pos", "symbol"])

_OPCODE_TO_BINARY: dict[Opcode, int] = {op: op.value for op in Opcode}
_BINARY_TO_OPCODE: dict[int, Opcode] = {op.value: op for op in Opcode}

_MODE_TO_BINARY: dict[Mode, int] = {m: m.value for m in Mode}
_BINARY_TO_MODE: dict[int, Mode] = {m.value: m for m in Mode}

SPECIAL_MNEMONICS: dict[str, tuple[Opcode, Mode]] = {
    "ei": (Opcode.SPECIAL, Mode.EI),
    "di": (Opcode.SPECIAL, Mode.DI),
    "iret": (Opcode.SPECIAL, Mode.IRET),
    "inc": (Opcode.SPECIAL, Mode.INC),
    "dec": (Opcode.SPECIAL, Mode.DEC),
    "not": (Opcode.SPECIAL, Mode.NOT),
    "ret": (Opcode.SPECIAL, Mode.RET),
    "halt": (Opcode.SPECIAL, Mode.HALT),
}

MNEMONIC_TO_OPCODE_MODE: dict[str, tuple[Opcode, Mode | None]] = {
    "nop": (Opcode.NOP, None),
    "load": (Opcode.LOAD, None),
    "store": (Opcode.STORE, None),
    "add": (Opcode.ADD, None),
    "sub": (Opcode.SUB, None),
    "and": (Opcode.AND, None),
    "or": (Opcode.OR, None),
    "jmp": (Opcode.JMP, None),
    "jz": (Opcode.JZ, None),
    "jn": (Opcode.JN, None),
    "call": (Opcode.CALL, None),
    "push": (Opcode.PUSH, None),
    "pop": (Opcode.POP, None),
    "jc": (Opcode.JC, None),
    "jnc": (Opcode.JNC, None),
    **{k: (v[0], v[1]) for k, v in SPECIAL_MNEMONICS.items()},
}

OPCODE_MODE_TO_MNEMONIC: dict[tuple[Opcode, Mode | None], str] = {
    (Opcode.NOP, None): "nop",
    (Opcode.LOAD, None): "load",
    (Opcode.STORE, None): "store",
    (Opcode.ADD, None): "add",
    (Opcode.SUB, None): "sub",
    (Opcode.AND, None): "and",
    (Opcode.OR, None): "or",
    (Opcode.JMP, None): "jmp",
    (Opcode.JZ, None): "jz",
    (Opcode.JN, None): "jn",
    (Opcode.CALL, None): "call",
    (Opcode.PUSH, None): "push",
    (Opcode.POP, None): "pop",
    (Opcode.JC, None): "jc",
    (Opcode.JNC, None): "jnc",
    **{(v[0], v[1]): k for k, v in SPECIAL_MNEMONICS.items()},
}


def to_bytes(code: list[dict]) -> bytes:
    result = bytearray()
    for instr in code:
        opcode = _OPCODE_TO_BINARY[instr["opcode"]]
        mode = _MODE_TO_BINARY.get(instr.get("mode", Mode.ABSOLUTE), 0)
        arg = instr.get("arg", 0) & 0xFFFFFF
        word = (opcode << 28) | (mode << 24) | arg
        result.extend(struct.pack(">I", word))
    return bytes(result)


def from_bytes(binary_code: bytes) -> list[dict]:
    structured: list[dict] = []
    for i in range(0, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break
        word = struct.unpack(">I", binary_code[i : i + 4])[0]
        opcode = _BINARY_TO_OPCODE[(word >> 28) & 0xF]
        mode = _BINARY_TO_MODE.get((word >> 24) & 0xF, Mode.ABSOLUTE)
        arg = word & 0xFFFFFF
        if arg >= 0x800000:
            arg -= 0x1000000
        instr: dict = {"index": i // 4, "opcode": opcode, "mode": mode, "arg": arg}
        structured.append(instr)
    return structured


def to_hex(code: list[dict]) -> str:
    binary = to_bytes(code)
    lines: list[str] = []
    for i in range(0, len(binary), 4):
        if i + 3 >= len(binary):
            break
        word = struct.unpack(">I", binary[i: i + 4])[0]
        opcode = _BINARY_TO_OPCODE[(word >> 28) & 0xF]
        mode = _BINARY_TO_MODE.get((word >> 24) & 0xF, Mode.ABSOLUTE)
        arg = word & 0xFFFFFF
        display_arg = arg
        if display_arg >= 0x800000:
            display_arg -= 0x1000000

        mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, mode if opcode == Opcode.SPECIAL else None))
        if mnemonic is None:
            mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, None), "???")

        if opcode not in (Opcode.NOP, Opcode.SPECIAL, Opcode.PUSH, Opcode.POP):
            is_address = mode in (Mode.ABSOLUTE, Mode.INDIRECT) or opcode in (
                Opcode.JMP, Opcode.JZ, Opcode.JN, Opcode.CALL, Opcode.JC, Opcode.JNC
            )

            if is_address:
                addr = int(arg) & 0xFFFFFF
                if addr < 0x100:
                    arg_str = f"0x{addr:02X}"
                elif addr < 0x10000:
                    arg_str = f"0x{addr:04X}"
                else:
                    arg_str = f"0x{addr:06X}"
                mnemonic = f"{mnemonic} {arg_str}"
            else:
                mnemonic = f"{mnemonic} {display_arg}"

        lines.append(f"{i // 4} - {word:08X} - {mnemonic}")
    return "\n".join(lines)

def write_json(filename: str, code: list[dict]) -> None:
    buf: list[str] = []
    for instr in code:
        entry = {"index": instr["index"], "opcode": instr["opcode"].name, "mode": instr.get("mode", Mode.ABSOLUTE).name}
        if "arg" in instr:
            entry["arg"] = instr["arg"]
        if "term" in instr:
            entry["term"] = instr["term"]
        buf.append(json.dumps(entry))
    with open(filename, "w", encoding="utf-8") as f:
        f.write("[" + ",\n ".join(buf) + "]")