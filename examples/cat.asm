.equ OUTPUT_PORT 0xFFFFF1
.equ INPUT_PORT  0xFFFFF0

.section .text
.org 0x00
start:
    EI
loop:
    JMP loop

.org 0x10
handler:
    LOAD INPUT_PORT
    JZ stop
    STORE OUTPUT_PORT
    IRET
stop:
    HALT