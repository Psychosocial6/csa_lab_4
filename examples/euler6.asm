.equ OUTPUT_PORT 0xFFFFF4

.section .data
N: .word 10
sum: .word 0
sum_sq: .word 0
sq_sum: .word 0
result: .word 0
digit_buf:
    .word 0
    .word 0
    .word 0
    .word 0
    .word 0
    .word 0
    .word 0
    .word 0
digit_ptr:
    .word 0
i:
    .word 0
msg: .string "2640\n"

.section .text
start:
    ; Compute sum of squares and sum
    LOAD #1
    STORE i
loop:
    LOAD i
    SUB N
    JZ loop_done
    JN loop_continue
    JMP loop_done
loop_continue:
    ; sum += i
    LOAD sum
    ADD i
    STORE sum
    ; sum_sq += i*i
    LOAD i
    MUL i
    STORE temp
    LOAD sum_sq
    ADD temp
    STORE sum_sq
    ; i++
    LOAD i
    ADD #1
    STORE i
    JMP loop
loop_done:
    ; Add N to sum and N*N to sum_sq
    LOAD sum
    ADD N
    STORE sum
    LOAD N
    MUL N
    STORE temp
    LOAD sum_sq
    ADD temp
    STORE sum_sq
    ; sq_sum = sum * sum
    LOAD sum
    MUL sum
    STORE sq_sum
    ; result = sq_sum - sum_sq
    LOAD sq_sum
    SUB sum_sq
    STORE result
    ; Print result
    STORE OUTPUT_PORT
    HALT

.section .data
temp:
    .word 0
ptr:
    .word 0
