.equ OUTPUT_PORT 0xFFFFF1
.equ OUTPUT_NUM_PORT 0xFFFFF2
.equ PRINT_SPACE 1
.macro PRINT_SPACE_CHAR
    LOAD #32
    STORE OUTPUT_PORT
.endmacro

.section .data
a_high: .word 1
a_low:  .word 0xFFFFFFFF
b_high: .word 0
b_low:  .word 2
r_high: .word 0
r_low:  .word 0

.section .text
start:
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