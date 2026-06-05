from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass

from isa import (
    DEFAULT_IVT_INPUT,
    INPUT_PORT,
    IVT_INPUT,
    OUTPUT_NUM_PORT,
    OUTPUT_PORT,
    Mode,
    Opcode,
    from_bytes,
    OPCODE_MODE_TO_MNEMONIC,
)


@dataclass
class PS:
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
        self.psw = PS()
        self.psw.update(self.acc)
        self.input_port_value = 0
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
            return self.input_port_value
        if addr == OUTPUT_PORT:
            return 0
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

    def alu_op(self, operation: Opcode | Mode, operand: int) -> tuple[int, bool]:
        result = self.acc
        carry = False

        if isinstance(operation, Opcode):
            if operation == Opcode.ADD:
                raw = (self.acc & 0xFFFFFFFF) + (operand & 0xFFFFFFFF)
                carry = raw > 0xFFFFFFFF
                result = raw
                if result >= 0x80000000:
                    result -= 0x100000000
            elif operation == Opcode.SUB:
                raw = (self.acc & 0xFFFFFFFF) - (operand & 0xFFFFFFFF)
                carry = raw < 0
                result = raw
                if result >= 0x80000000:
                    result -= 0x100000000
            elif operation == Opcode.AND:
                result = self.acc & operand
            elif operation == Opcode.OR:
                result = self.acc | operand
        elif isinstance(operation, Mode):
            if operation == Mode.INC:
                result = self.acc + 1
            elif operation == Mode.DEC:
                result = self.acc - 1
            elif operation == Mode.NOT:
                result = ~self.acc

        return result, carry


def format_instruction(instr: dict | None) -> str:
    if instr is None:
        return "-"

    opcode = instr["opcode"]
    mode = instr.get("mode", Mode.ABSOLUTE)
    arg = instr.get("arg", "")

    if opcode == Opcode.SPECIAL:
        mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, mode))
    else:
        mnemonic = OPCODE_MODE_TO_MNEMONIC.get((opcode, None))

    if mnemonic is None:
        mnemonic = opcode.name

    has_no_arg = opcode == Opcode.SPECIAL or opcode == Opcode.NOP or opcode in (Opcode.PUSH, Opcode.POP)

    if has_no_arg or arg == "":
        return mnemonic

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
    else:
        arg_str = str(arg)

    return f"{mnemonic} {arg_str}".strip()


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

        self.current_instr: dict | None = None
        self.busy_ticks = 0
        self.irq_transition = False
        self._halt_pending = False
        self.irq_pending = False  # Флаг запроса прерывания

    def current_tick(self) -> int:
        return self.tick

    def check_interrupt(self) -> bool:
        return self.irq_pending and self.data_path.psw.IEF

    def get_instruction_cycles(self, instr: dict) -> int:
        opcode = instr["opcode"]
        mode = instr.get("mode", Mode.ABSOLUTE)

        if opcode == Opcode.NOP:
            return 2

        if opcode in (Opcode.LOAD, Opcode.ADD, Opcode.SUB, Opcode.AND, Opcode.OR):
            if mode == Mode.IMMEDIATE:
                return 4
            if mode == Mode.ABSOLUTE:
                return 5
            if mode == Mode.INDIRECT:
                return 7

        if opcode == Opcode.STORE:
            if mode == Mode.ABSOLUTE:
                return 4
            if mode == Mode.INDIRECT:
                return 7

        if opcode in (Opcode.JMP, Opcode.JZ, Opcode.JN, Opcode.CALL, Opcode.JC, Opcode.JNC):
            return 3

        if opcode == Opcode.PUSH:
            return 4

        if opcode == Opcode.POP:
            return 5

        if opcode == Opcode.SPECIAL:
            special_mode = instr.get("mode", Mode.ABSOLUTE)
            if special_mode == Mode.HALT:
                return 2
            if special_mode in (Mode.EI, Mode.DI, Mode.INC, Mode.DEC, Mode.NOT):
                return 3
            if special_mode == Mode.RET:
                return 5
            if special_mode == Mode.IRET:
                return 7

        return 1

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

        next_pc = instr["index"] + 1
        self.pc = next_pc

        if opcode == Opcode.NOP:
            return

        if opcode == Opcode.LOAD:
            val = self.fetch_operand(instr)
            self.data_path.signal_latch_acc(val)
            return

        if opcode == Opcode.STORE:
            addr = arg if mode != Mode.INDIRECT else self.data_path.signal_rd(arg)
            self.data_path.signal_wr(addr, self.data_path.acc)
            return

        if opcode in (Opcode.ADD, Opcode.SUB, Opcode.AND, Opcode.OR):
            operand = self.fetch_operand(instr)
            result, carry = self.data_path.alu_op(opcode, operand)
            self.data_path.signal_latch_acc(result)
            self.data_path.psw.C = carry
            return

        if opcode == Opcode.PUSH:
            self.data_path.signal_push(self.data_path.acc)
            return

        if opcode == Opcode.POP:
            self.data_path.signal_latch_acc(self.data_path.signal_pop())
            return

        if opcode == Opcode.JC:
            if self.data_path.psw.C:
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
            return

        if opcode == Opcode.JNC:
            if not self.data_path.psw.C:
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
            return

        if opcode == Opcode.JMP:
            if mode == Mode.RELATIVE:
                self.pc = next_pc + arg
            else:
                self.pc = arg
            return

        if opcode == Opcode.JZ:
            if self.data_path.psw.Z:
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
            return

        if opcode == Opcode.JN:
            if self.data_path.psw.N:
                if mode == Mode.RELATIVE:
                    self.pc = next_pc + arg
                else:
                    self.pc = arg
            return

        if opcode == Opcode.CALL:
            self.data_path.signal_push(next_pc)
            if mode == Mode.RELATIVE:
                self.pc = next_pc + arg
            else:
                self.pc = arg
            return

        if opcode == Opcode.SPECIAL:
            special_mode = instr.get("mode", Mode.ABSOLUTE)
            if special_mode == Mode.HALT:
                self._halt_pending = True
                return
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
            elif special_mode == Mode.INC:
                result, _ = self.data_path.alu_op(special_mode, 0)
                self.data_path.signal_latch_acc(result)
            elif special_mode == Mode.DEC:
                result, _ = self.data_path.alu_op(special_mode, 0)
                self.data_path.signal_latch_acc(result)
            elif special_mode == Mode.NOT:
                result, _ = self.data_path.alu_op(special_mode, 0)
                self.data_path.signal_latch_acc(result)
            elif special_mode == Mode.RET:
                self.pc = self.data_path.signal_pop()
                self.in_interrupt = False
            return

    def process_next_tick(self) -> None:
        self.tick += 1

        # Изменено строгое равенство (==) на нестрогое (<=)
        arrived_char = None
        while (self.interrupt_index < len(self.interrupt_schedule) and
               self.interrupt_schedule[self.interrupt_index][0] <= self.tick):
            arrived_char = self.interrupt_schedule[self.interrupt_index][1]
            self.interrupt_index += 1

        if arrived_char is not None:
            self.data_path.input_port_value = ord(arrived_char)
            self.irq_pending = True
            logging.debug("INPUT PORT OVERWRITE at tick %d: char=%s", self.tick, repr(arrived_char))

        # 2. Если процессор выполняет текущую инструкцию
        if self.busy_ticks > 0:
            self.busy_ticks -= 1
            if self.busy_ticks == 0:
                if self._halt_pending:
                    self.halted = True
                if self.irq_transition:
                    self.irq_transition = False
            return

        # 3. Обработка прерывания
        if self.check_interrupt():
            self.irq_pending = False
            logging.debug("INTERRUPT TRIGGERED at tick %d", self.tick)

            resume_pc = self.pc
            flags_val = int(self.data_path.psw.Z) | (int(self.data_path.psw.N) << 1) | (
                        int(self.data_path.psw.C) << 2)
            self.data_path.signal_push(resume_pc)
            self.data_path.signal_push(flags_val)

            ivt_addr = self.data_path.signal_rd(IVT_INPUT)
            self.pc = ivt_addr

            self.data_path.psw.IEF = False
            self.in_interrupt = True
            self.current_instr = None
            self.irq_transition = True
            self.busy_ticks = 3 - 1
            return

        # 4. Выполнение следующей инструкции
        if self.pc < len(self.program):
            instr = self.program[self.pc]
            self.current_instr = instr
            cycles = self.get_instruction_cycles(instr)
            self.execute_instruction(instr)
            self.busy_ticks = cycles - 1
            if self.busy_ticks == 0:
                if self._halt_pending:
                    self.halted = True
        else:
            self.current_instr = None
            self.halted = True

    def __repr__(self) -> str:
        instr_str = format_instruction(self.current_instr)
        state_repr = (
            f"TICK: {self.tick:3} PC: {self.pc:3} | "
            f"INSTR: {instr_str:<12} | "
            f"ACC: {self.data_path.acc:5} | PSW: {self.data_path.psw}"
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