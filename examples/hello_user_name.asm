.equ OUTPUT_PORT 0xFFFFF1
.equ INPUT_PORT  0xFFFFF0
.equ IVT_INPUT   0xFFFFF3
.equ NAME_START  0x200

.section .data
greeting: .string "Hello, "
name_ptr: .word 0
input_done: .word 0
end_msg: .string "!\n"
ptr: .word 0

.section .text
.org 0x10
handler:
    LOAD INPUT_PORT
    JZ done_isr
    STORE [name_ptr]
    LOAD name_ptr
    INC
    STORE name_ptr
    IRET

done_isr:
    LOAD #1
    STORE input_done
    LOAD #0
    STORE [name_ptr]
    IRET

start:
    LOAD #0x10
    STORE IVT_INPUT
    LOAD #NAME_START
    STORE name_ptr
    EI

wait:
    LOAD input_done
    JZ wait
    LOAD #greeting
    CALL print_string
    LOAD #NAME_START
    CALL print_string
    LOAD #end_msg
    CALL print_string
    HALT

print_string:
    STORE ptr

ps_loop:
    LOAD [ptr]
    JZ ps_done
    STORE OUTPUT_PORT
    LOAD ptr
    INC
    STORE ptr
    JMP ps_loop

ps_done:
    RET