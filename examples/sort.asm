.equ OUTPUT_PORT 0xFFFFF1

.section .data
array:
    .word 53   ; '5'
    .word 51   ; '3'
    .word 56   ; '8'
    .word 49   ; '1'
    .word 52   ; '4'
    .word 0
array_len: .word 5
i: .word 0
j: .word 0
temp: .word 0
ptr: .word 0
ptr2: .word 0

.section .text
start:

outer_loop:
    LOAD i
    SUB array_len
    JZ outer_done
    LOAD #0
    STORE j

inner_loop:
    LOAD j
    SUB array_len
    ADD #1
    ADD i
    JZ inner_done
    LOAD #array
    ADD j
    STORE ptr
    INC
    STORE ptr2
    LOAD [ptr]
    STORE temp
    LOAD [ptr2]
    SUB temp
    JN do_swap
    JMP no_swap

do_swap:
    LOAD [ptr2]
    STORE [ptr]
    LOAD temp
    STORE [ptr2]

no_swap:
    LOAD j
    INC
    STORE j
    JMP inner_loop

inner_done:
    LOAD i
    INC
    STORE i
    JMP outer_loop

outer_done:
    LOAD #array
    CALL print_array
    HALT

print_array:
    STORE ptr

pa_loop:
    LOAD [ptr]
    JZ pa_done
    STORE OUTPUT_PORT
    LOAD ptr
    INC
    STORE ptr
    JMP pa_loop

pa_done:
    RET