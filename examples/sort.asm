.equ OUTPUT_PORT 0xFFFFF1

.section .data
array:
    .word 53   ; '5'
    .word 51   ; '3'
    .word 56   ; '8'
    .word 49   ; '1'
    .word 52   ; '4'
    .word 0
array_len:
    .word 5
i:
    .word 0
j:
    .word 0
temp:
    .word 0
temp2:
    .word 0
ptr:
    .word 0

.section .text
start:
    LOAD #0
    STORE i
outer_loop:
    LOAD i
    SUB array_len
    JZ outer_done
    JN outer_continue
    JMP outer_done
outer_continue:
    LOAD #0
    STORE j
inner_loop:
    LOAD j
    SUB array_len
    ADD #1
    ADD i
    JZ inner_done
    JN inner_continue
    JMP inner_done
inner_continue:
    ; ptr = &array[j]
    LOAD #array
    ADD j
    STORE ptr
    ; temp = array[j]
    LOAD [ptr]
    STORE temp
    ; ptr = &array[j+1]
    LOAD ptr
    ADD #1
    STORE ptr
    ; acc = array[j+1] - array[j]
    LOAD [ptr]
    SUB temp
    JN do_swap
    JZ no_swap
    JMP no_swap
do_swap:
    ; Swap array[j] and array[j+1]
    ; temp2 = array[j+1]
    LOAD [ptr]
    STORE temp2
    ; ptr = &array[j]
    LOAD ptr
    SUB #1
    STORE ptr
    ; array[j] = temp2
    LOAD temp2
    STORE [ptr]
    ; ptr = &array[j+1]
    LOAD ptr
    ADD #1
    STORE ptr
    ; array[j+1] = temp
    LOAD temp
    STORE [ptr]
no_swap:
    LOAD j
    ADD #1
    STORE j
    JMP inner_loop
inner_done:
    LOAD i
    ADD #1
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
    ADD #1
    STORE ptr
    JMP pa_loop
pa_done:
    RET
