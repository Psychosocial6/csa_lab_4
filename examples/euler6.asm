.equ OUTPUT_PORT 0xFFFFF1

.section .data
N: .word 10
sum: .word 0
sum_sq: .word 0
sq_sum: .word 0
result: .word 0
i: .word 0
temp: .word 0
mul_arg1: .word 0
mul_arg2: .word 0
mul_res:  .word 0

.section .text
start:
    LOAD #1
    STORE i

loop:
    LOAD N
    SUB i
    JN loop_done
    LOAD sum
    ADD i
    STORE sum
    LOAD i
    STORE mul_arg1
    STORE mul_arg2
    CALL multiply
    STORE temp
    LOAD sum_sq
    ADD temp
    STORE sum_sq
    LOAD i
    INC
    STORE i
    JMP loop

loop_done:
    LOAD sum
    STORE mul_arg1
    STORE mul_arg2
    CALL multiply
    STORE sq_sum
    LOAD sq_sum
    SUB sum_sq
    STORE result
    STORE OUTPUT_PORT
    HALT

multiply:
    LOAD #0
    STORE mul_res

multiply_loop:
    LOAD mul_arg2
    JZ multiply_done
    DEC
    STORE mul_arg2
    LOAD mul_res
    ADD mul_arg1
    STORE mul_res
    JMP multiply_loop

multiply_done:
    LOAD mul_res
    RET