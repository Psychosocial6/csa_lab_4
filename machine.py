from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

from isa import (
    DEFAULT_IVT_INPUT,
    IE_REG,
    INPUT_PORT,
    IVT_INPUT,
    OUTPUT_PORT,
    OUTPUT_NUM_PORT,
    Mode,
    Opcode,
    from_bytes,
)


@dataclass
class PSW:
    Z: bool = False
    N: bool = False
    C: bool = False
    IEF: bool = True

    def update(self, value: int, carry: bool = False) -> None:
        self.Z = value == 0
        self.N = value < 0
        self.C = carry

    def __repr__(self) -> str:
        return f"Z={int(self.Z)} N={int(self.N)} C={int(self.C)} IEF={int(self.IEF)}"


class DataPath:
    def __init__(self, data_memory_size: int, initial_data: list[tuple[int, int]]) -> None:
        assert data_memory_size > 0
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        for addr, val in initial_data:
            if 0 <= addr < data_memory_size:
                self.data_memory[addr] = val
        self.acc = 0
        self.sp = data_memory_size - 1
        self.psw = PSW()
        self.input_buffer: list[str] = []
        self.output_buffer: list[str] = []
        self._input_port_ready = False
        self._input_port_char = "\0"

    def signal_latch_acc(self, value: int) -> None:
        self.acc = value & 0xFFFFFFFF
        if self.acc >= 0x80000000:
            self.acc -= 0x100000000
        self.psw.update(self.acc)

    def signal_rd(self, addr: int) -> int:
        addr = addr & 0xFFFFFF
        if addr == INPUT_PORT:
            if self.input_buffer:
                ch = self.input_buffer.pop(0)
                return ord(ch)
            return 0
        if addr == OUTPUT_PORT:
            return 0
        if addr == IE_REG:
            return int(self.psw.IEF)
        if addr == IVT_INPUT:
            return DEFAULT_IVT_INPUT
        if 0 <= addr < self.data_memory_size:
            return self.data_memory[addr]
        return 0

    def signal_wr(self, addr: int, value: int) -> None:
        addr = addr & 0xFFFFFF
        value = value & 0xFFFFFFFF
        if value >= 0x80000000:
            value -= 0x100000000
        if addr == OUTPUT_PORT:
            char = chr(value & 0xFF)
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(char))
            self.output_buffer.append(char)
            return
        if addr == OUTPUT_NUM_PORT:
            num_str = str(value)
            for ch in num_str:
                self.output_buffer.append(ch)
            logging.debug("output_num: %s << %s", repr("".join(self.output_buffer)), num_str)
        if addr == IE_REG:
            self.psw.IEF = bool(value & 1)
            return
        if 0 <= addr < self.data_memory_size:
            self.data_memory[addr] = value

    def signal_push(self, value: int) -> None:
        self.signal_wr(self.sp, value)
        self.sp -= 1
        if self.sp < 0:
            raise OverflowError("Stack overflow")

    def signal_pop(self) -> int:
        self.sp += 1
        if self.sp >= self.data_memory_size:
            raise OverflowError("Stack underflow")
        return self.signal_rd(self.sp)

    def alu_op(self, opcode: Opcode, operand: int) -> tuple[int, bool]:
        result = self.acc
        carry = False
        if opcode == Opcode.ADD:
            raw = (self.acc & 0xFFFFFFFF) + (operand & 0xFFFFFFFF)
            carry = raw > 0xFFFFFFFF
            result = raw
            if result >= 0x80000000:
                result -= 0x100000000
        elif opcode == Opcode.SUB:
            raw = (self.acc & 0xFFFFFFFF) - (operand & 0xFFFFFFFF)
            carry = raw < 0
            result = raw
            if result >= 0x80000000:
                result -= 0x100000000
        elif opcode == Opcode.MUL:
            result = self.acc * operand
        elif opcode == Opcode.DIV:
            if operand == 0:
                raise ZeroDivisionError("Division by zero")
            result = self.acc // operand
        elif opcode == Opcode.AND:
            result = self.acc & operand
        elif opcode == Opcode.OR:
            result = self.acc | operand
        elif opcode == Opcode.NOT:
            result = ~self.acc
        elif opcode == Mode.INC_ACC:
            result = self.acc + 1
        elif opcode == Mode.DEC_ACC:
            result = self.acc - 1
        return result, carry

    def zero(self) -> bool:
        return self.acc == 0

    def negative(self) -> bool:
        return self.acc < 0


@dataclass
class PipelineStage:
    name: str
    instr: dict[str, Any] | None = None
    bubble: bool = False

    def clear(self) -> None:
        self.instr = None
        self.bubble = False

    def set_bubble(self) -> None:
        self.instr = None
        self.bubble = True

    def __repr__(self) -> str:
        if self.bubble:
            return "BUBBLE"
        if self.instr is None:
            return "-"
        opcode = self.instr["opcode"].name
        arg = self.instr.get("arg", "")
        return f"{opcode} {arg}".strip()


class ControlUnit:
    def __init__(
        self,
        program: list[dict],
        data_path: DataPath,
        interrupt_schedule: list[tuple[int, str]],
    ) -> None:
        self.program = program
        self.pc = 0
        self.data_path = data_path
        self.tick = 0
        self.interrupt_schedule = sorted(interrupt_schedule, key=lambda x: x[0])
        self.interrupt_index = 0
        self.in_interrupt = False
        self.halted = False

        self.if_stage = PipelineStage("IF")
        self.id_stage = PipelineStage("ID")
        self.ex_stage = PipelineStage("EX")

    def current_tick(self) -> int:
        return self.tick

    def check_interrupt(self) -> str | None:
        if not self.data_path.psw.IEF:
            return None
        if self.interrupt_index >= len(self.interrupt_schedule):
            return None
        scheduled_tick, char = self.interrupt_schedule[self.interrupt_index]
        if scheduled_tick <= self.tick:
            self.interrupt_index += 1
            return char
        return None

    def handle_interrupt(self, char: str) -> None:
        logging.debug("INTERRUPT at tick %d: char=%s", self.tick, repr(char))
        self.data_path.psw.IEF = False
        self.data_path.signal_push(self.pc)
        self.data_path.signal_push(
            int(self.data_path.psw.Z) | (int(self.data_path.psw.N) << 1) | (int(self.data_path.psw.C) << 2)
        )
        ivt_addr = self.data_path.signal_rd(IVT_INPUT)
        self.pc = ivt_addr
        self.in_interrupt = True
        # Flush pipeline
        self.if_stage.clear()
        self.id_stage.clear()
        self.ex_stage.clear()
        self.stall = False

    def fetch_operand(self, instr: dict) -> int:
        mode = instr.get("mode", Mode.ABSOLUTE)
        arg = int(instr.get("arg", 0))
        if arg >= 0x800000:
            arg -= 0x1000000
        if mode == Mode.IMMEDIATE:
            return arg
        if mode == Mode.ABSOLUTE:
            return self.data_path.signal_rd(arg)
        if mode == Mode.INDIRECT:
            ptr = self.data_path.signal_rd(arg)
            return self.data_path.signal_rd(ptr)
        if mode == Mode.RELATIVE:
            return arg
        return arg

    def execute_instruction(self, instr: dict) -> None:
        opcode = instr["opcode"]
        mode = instr.get("mode", Mode.ABSOLUTE)
        arg = int(instr.get("arg", 0))
        if arg >= 0x800000:
            arg -= 0x1000000

        if opcode == Opcode.HALT:
            self.halted = True
            return

        if opcode == Opcode.LOAD:
            val = self.fetch_operand(instr)
            self.data_path.signal_latch_acc(val)
            return

        if opcode == Opcode.STORE:
            addr = arg if mode != Mode.INDIRECT else self.data_path.signal_rd(arg)
            self.data_path.signal_wr(addr, self.data_path.acc)
            return

        if opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.AND, Opcode.OR):
            operand = self.fetch_operand(instr)
            result, carry = self.data_path.alu_op(opcode, operand)
            self.data_path.signal_latch_acc(result)
            self.data_path.psw.C = carry
            return

        if opcode == Opcode.NOT:
            result, _ = self.data_path.alu_op(opcode, 0)
            self.data_path.signal_latch_acc(result)
            return

        next_pc = instr["index"] + 1

        if opcode == Opcode.JMP:
            if mode == Mode.RELATIVE:
                self.pc = next_pc + arg
            else:
                self.pc = arg
            self.if_stage.clear()
            self.id_stage.clear()
            return

        if opcode == Opcode.JZ:
            if self.data_path.zero():
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
                self.if_stage.clear()
                self.id_stage.clear()
            return

        if opcode == Opcode.JN:
            if self.data_path.negative():
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
                self.if_stage.clear()
                self.id_stage.clear()
            return

        if opcode == Opcode.CALL:
            self.data_path.signal_push(next_pc)
            if mode == Mode.RELATIVE:
                self.pc = next_pc + arg
            else:
                self.pc = arg
            self.if_stage.clear()
            self.id_stage.clear()
            return

        if opcode == Opcode.RET:
            self.pc = self.data_path.signal_pop()
            self.in_interrupt = False
            self.if_stage.clear()
            self.id_stage.clear()
            return

        if opcode == Opcode.SPECIAL:
            special_mode = instr.get("mode", Mode.ABSOLUTE)
            if special_mode == Mode.PUSH:
                self.data_path.signal_push(self.data_path.acc)
            elif special_mode == Mode.POP:
                self.data_path.signal_latch_acc(self.data_path.signal_pop())
            elif special_mode == Mode.EI:
                self.data_path.psw.IEF = True
            elif special_mode == Mode.DI:
                self.data_path.psw.IEF = False
            elif special_mode == Mode.IRET:
                flags = self.data_path.signal_pop()
                self.pc = self.data_path.signal_pop()
                self.data_path.psw.Z = bool(flags & 1)
                self.data_path.psw.N = bool(flags & 2)
                self.data_path.psw.C = bool(flags & 4)
                self.data_path.psw.IEF = True
                self.in_interrupt = False
                self.if_stage.clear()
                self.id_stage.clear()
            elif special_mode == Mode.INC_ACC:
                result, _ = self.data_path.alu_op(special_mode, 0)
                self.data_path.signal_latch_acc(result)
            elif special_mode == Mode.DEC_ACC:
                result, _ = self.data_path.alu_op(special_mode, 0)
                self.data_path.signal_latch_acc(result)
            elif special_mode == Mode.JC:
                if self.data_path.psw.C:
                    if mode == Mode.RELATIVE:
                        self.pc = next_pc + arg
                    else:
                        self.pc = arg
                    self.if_stage.clear()
                    self.id_stage.clear()
                return
            elif special_mode == Mode.JNC:
                if not self.data_path.psw.C:
                    if mode == Mode.RELATIVE:
                        self.pc = next_pc + arg
                    else:
                        self.pc = arg
                    self.if_stage.clear()
                    self.id_stage.clear()
                return
            return

    def process_next_tick(self) -> None:
        self.tick += 1

        char = self.check_interrupt()
        if char is not None:
            self.data_path.input_buffer.append(char)
            self.handle_interrupt(char)
            return

        self.ex_stage.instr = self.id_stage.instr
        self.ex_stage.bubble = self.id_stage.bubble

        self.id_stage.instr = self.if_stage.instr
        self.id_stage.bubble = self.if_stage.bubble

        if self.pc < len(self.program):
            self.if_stage.instr = self.program[self.pc]
            self.if_stage.bubble = False
            self.pc += 1
        else:
            self.if_stage.clear()

        if self.ex_stage.instr is not None and not self.ex_stage.bubble:
            self.execute_instruction(self.ex_stage.instr)

    def __repr__(self) -> str:
        state_repr = (
            f"TICK: {self.tick:3} PC: {self.pc:3} | "
            f"IF: {self.if_stage} | ID: {self.id_stage} | EX: {self.ex_stage} | "
            f"ACC: {self.data_path.acc} | PSW: {self.data_path.psw}"
        )
        if self.in_interrupt:
            state_repr += " [IRQ]"
        return state_repr


def simulation(
    code: list[dict],
    data: list[tuple[int, int]],
    interrupt_schedule: list[tuple[int, str]],
    data_memory_size: int = 1024,
    limit: int = 10000,
) -> tuple[str, int]:
    data_path = DataPath(data_memory_size, data)
    control_unit = ControlUnit(code, data_path, interrupt_schedule)

    logging.debug("%s", control_unit)

    try:
        while control_unit.tick < limit and not control_unit.halted:
            control_unit.process_next_tick()
            logging.debug("%s", control_unit)
    except (ZeroDivisionError, OverflowError):
        logging.exception("Runtime error")

    if control_unit.tick >= limit:
        logging.warning("Limit exceeded!")

    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), control_unit.tick


def main(code_file: str, input_file: str | None = None) -> None:
    with open(code_file, "rb") as f:
        binary_code = f.read()
    code = from_bytes(binary_code)

    data: list[tuple[int, int]] = []
    data_json = code_file + ".data.json"
    if input_file is not None:
        data_json = code_file + ".data.json"
    try:
        with open(data_json, encoding="utf-8") as f:
            raw = json.load(f)
            data = [(d[0], d[1]) for d in raw.get("data", [])]
    except FileNotFoundError:
        pass

    interrupt_schedule: list[tuple[int, str]] = []
    if input_file:
        try:
            with open(input_file, encoding="utf-8") as f:
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
        except FileNotFoundError:
            pass

    output, ticks = simulation(code, data, interrupt_schedule, data_memory_size=1024, limit=10000)
    print(output)
    print("ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    if len(sys.argv) >= 2:
        code_file = sys.argv[1]
        input_file = sys.argv[2] if len(sys.argv) > 2 else None
        main(code_file, input_file)
    else:
        print("Usage: machine.py <code.bin> [<input_schedule.txt>]")
