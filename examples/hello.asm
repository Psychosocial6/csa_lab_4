.equ OUTPUT_PORT 0xFFFFF1

.section .data
msg: .string "Hello, World!\n"
str_addr: .word 0

.section .text
start:
    LOAD #msg
    CALL print_string
    HALT

print_string:
    STORE str_addr

loop:
    LOAD [str_addr]
    JZ done
    STORE OUTPUT_PORT
    LOAD str_addr
    ADD #4
    STORE str_addr
    JMP loop

done:
    RET