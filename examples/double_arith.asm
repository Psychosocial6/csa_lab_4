.equ OUTPUT_PORT 0xFFFFF1
.equ OUTPUT_NUM_PORT 0xFFFFF4

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
    JC has_carry
    LOAD #0
    STORE r_high
    JMP add_high
has_carry:
    LOAD #1
    STORE r_high
add_high:
    LOAD a_high
    ADD b_high
    ADD r_high
    STORE r_high
    LOAD r_high
    STORE OUTPUT_NUM_PORT
    LOAD #32
    STORE OUTPUT_PORT
    LOAD r_low
    STORE OUTPUT_NUM_PORT
    HALT