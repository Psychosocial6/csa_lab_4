.equ OUTPUT_PORT 0xFFFFF1
.equ OUTPUT_NUM_PORT 0xFFFFF2
.equ INPUT_PORT  0xFFFFF0
.equ IVT_INPUT   0xFFFFF3
.equ PRINT_SPACE 1

.macro PRINT_SPACE_CHAR
    LOAD #32
    STORE OUTPUT_PORT
.endmacro

.section .data
a_high: .word 0
a_low:  .word 0
b_high: .word 0
b_low:  .word 0
r_high: .word 0
r_low:  .word 0
input_ptr: .word 0
input_count: .word 0
input_done: .word 0

.section .text
.org 0x10
handler:
    LOAD INPUT_PORT
    SUB #48
    STORE [input_ptr]
    LOAD input_ptr
    INC
    STORE input_ptr
    LOAD input_count
    INC
    STORE input_count
    SUB #4
    JZ all_done
    IRET

all_done:
    LOAD #1
    STORE input_done
    IRET

start:
    LOAD #a_high
    STORE input_ptr
    LOAD #0
    STORE input_count
    LOAD #0
    STORE input_done
    EI

wait_loop:
    LOAD input_done
    JZ wait_loop
    DI
    LOAD a_low
    ADD b_low
    STORE r_low
    JC low_carry
    LOAD a_high
    ADD b_high
    STORE r_high
    JMP print_res

low_carry:
    LOAD a_high
    ADD b_high
    INC
    STORE r_high

print_res:
    STORE OUTPUT_NUM_PORT
.if PRINT_SPACE
    PRINT_SPACE_CHAR
.endif
    LOAD r_low
    STORE OUTPUT_NUM_PORT
    HALT