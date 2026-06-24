from __future__ import annotations

import struct
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


class AddressingMode(int, Enum):
    ABSOLUTE = 0x0
    IMMEDIATE = 0x1
    INDIRECT = 0x2
    RELATIVE = 0x3


class SpecialOpcode(int, Enum):
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
IVT_INPUT = 0xFFFFF2
DEFAULT_IVT_INPUT = 0x10


_BINARY_TO_OPCODE: dict[int, Opcode] = {op.value: op for op in Opcode}
_BINARY_TO_ADDRESSING_MODE: dict[int, AddressingMode] = {m.value: m for m in AddressingMode}
_BINARY_TO_SPECIAL_OPCODE: dict[int, SpecialOpcode] = {s.value: s for s in SpecialOpcode}

SPECIAL_MNEMONICS: dict[str, tuple[Opcode, SpecialOpcode]] = {
    "ei": (Opcode.SPECIAL, SpecialOpcode.EI),
    "di": (Opcode.SPECIAL, SpecialOpcode.DI),
    "iret": (Opcode.SPECIAL, SpecialOpcode.IRET),
    "inc": (Opcode.SPECIAL, SpecialOpcode.INC),
    "dec": (Opcode.SPECIAL, SpecialOpcode.DEC),
    "not": (Opcode.SPECIAL, SpecialOpcode.NOT),
    "ret": (Opcode.SPECIAL, SpecialOpcode.RET),
    "halt": (Opcode.SPECIAL, SpecialOpcode.HALT),
}

MNEMONIC_TO_OPCODE_MODE: dict[str, tuple[Opcode, AddressingMode | SpecialOpcode | None]] = {
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

OPCODE_MODE_TO_MNEMONIC: dict[tuple[Opcode, AddressingMode | SpecialOpcode | None], str] = {
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


def to_bytes(code: list[dict], start_addr: int = 0) -> bytes:
    result = bytearray()
    result.extend(struct.pack(">I", start_addr))
    for instr in code:
        opcode = instr["opcode"]

        default_mode = SpecialOpcode.HALT if opcode == Opcode.SPECIAL else AddressingMode.ABSOLUTE
        mode = int(instr.get("mode", default_mode))

        arg = instr.get("arg", 0) & 0xFFFFFF
        word = (opcode << 28) | (mode << 24) | arg
        result.extend(struct.pack(">I", word))
    return bytes(result)


def from_bytes(binary_code: bytes) -> tuple[list[dict], int]:
    structured: list[dict] = []
    start_addr = struct.unpack(">I", binary_code[0:4])[0]
    for i in range(4, len(binary_code), 4):
        if i + 3 >= len(binary_code):
            break
        word = struct.unpack(">I", binary_code[i : i + 4])[0]
        opcode = _BINARY_TO_OPCODE[(word >> 28) & 0xF]
        mode_val = (word >> 24) & 0xF

        if opcode == Opcode.SPECIAL:
            mode: AddressingMode | SpecialOpcode = _BINARY_TO_SPECIAL_OPCODE.get(mode_val, SpecialOpcode.HALT)
        else:
            mode = _BINARY_TO_ADDRESSING_MODE.get(mode_val, AddressingMode.ABSOLUTE)

        arg = word & 0xFFFFFF
        if arg >= 0x800000:
            arg -= 0x1000000
        instr: dict = {"index": i - 4, "opcode": opcode, "mode": mode, "arg": arg}
        structured.append(instr)
    return structured, start_addr


def to_hex(code: list[dict]) -> str:
    binary = to_bytes(code)[4:]
    lines: list[str] = []
    for i in range(0, len(binary), 4):
        if i + 3 >= len(binary):
            break
        word = struct.unpack(">I", binary[i : i + 4])[0]
        opcode = _BINARY_TO_OPCODE[(word >> 28) & 0xF]
        mode_val = (word >> 24) & 0xF

        if opcode == Opcode.SPECIAL:
            mode: AddressingMode | SpecialOpcode = _BINARY_TO_SPECIAL_OPCODE.get(mode_val, SpecialOpcode.HALT)
        else:
            mode = _BINARY_TO_ADDRESSING_MODE.get(mode_val, AddressingMode.ABSOLUTE)

        arg = word & 0xFFFFFF
        display_arg = arg
        if display_arg >= 0x800000:
            display_arg -= 0x1000000

        mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, mode if opcode == Opcode.SPECIAL else None))
        if mnemonic is None:
            mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, None), "???")

        if opcode not in (Opcode.NOP, Opcode.SPECIAL, Opcode.PUSH, Opcode.POP):
            is_address = mode in (AddressingMode.ABSOLUTE, AddressingMode.INDIRECT) or opcode in (
                Opcode.JMP,
                Opcode.JZ,
                Opcode.JN,
                Opcode.CALL,
                Opcode.JC,
                Opcode.JNC,
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
