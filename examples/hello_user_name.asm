.equ OUTPUT_PORT 0xFFFFF1
.equ INPUT_PORT  0xFFFFF0
.equ IVT_INPUT   0xFFFFF3
.equ HEAP_START  0x200

.section .data
greeting: .string "Hello, "
name_ptr: .word 0
input_done: .word 0
end_msg: .string "!\n"
tmp: .word 0
tmp_char: .word 0

.section .text
.org 0
start:
    LOAD #0x10
    STORE IVT_INPUT
    LOAD #0
    STORE name_ptr
    ei

wait:
    LOAD input_done
    JZ wait

    LOAD #greeting
    CALL print_string

    LOAD #HEAP_START
    CALL print_string

    LOAD #end_msg
    CALL print_string
    HALT

.org 0x10
handler:
    LOAD INPUT_PORT
    JZ done
    STORE tmp_char
    LOAD name_ptr
    ADD #HEAP_START
    STORE tmp
    LOAD tmp_char
    STORE [tmp]
    LOAD name_ptr
    ADD #1
    STORE name_ptr
    iret

done:
    LOAD #1
    STORE input_done
    LOAD name_ptr
    ADD #HEAP_START
    STORE tmp
    LOAD #0
    STORE [tmp]
    iret
print_string:
    STORE ptr
ps_loop:
    LOAD [ptr]
    JZ ps_done
    STORE OUTPUT_PORT
    LOAD ptr
    ADD #1
    STORE ptr
    JMP ps_loop
ps_done:
    RET

.section .data
ptr: .word 0