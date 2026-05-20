# Лабораторная работа №4

- **ФИО:** Зыков Андрей Алексеевич
- **Группа:** P3206
- **Вариант:** `asm | acc | harv | hw | tick | binary | trap | mem | cstr | alg2 | pipeline`

## Язык программирования

---

Расширенная форма Бэкуса-Наура:

```
<program> ::= { <section_data> | <section_text> }

<section_data> ::= ".data" "\n" { <data_declaration> }

<data_declaration> ::= [ <label_def> ] ( <word_directive> | <string_directive> )

<word_directive> ::= ".word" <word_list> "\n"
<word_list> ::= <number_or_label> { "," <number_or_label> }

<string_directive> ::= ".string" <string_literal> "\n"
<string_literal> ::= '"' { <any_char_except_quote> | <escape_seq> } '"'
<escape_seq> ::= "\\n" | "\\t" | "\\\\" | "\\\""

<section_text> ::= ".text" "\n" { <code_line> }

<code_line> ::= [ <label_def> ] ( <directive> | <instruction> ) "\n"

<directive> ::= ".org" <number> | ".equ" <identifier> <number>

<label_def> ::= <identifier> ":"

<instruction> ::= <op_without_operand> | <op_with_operand> [ <operand> ]

<op_without_operand> ::= "halt" | "not" | "ret" | "push" | "pop" | "ei" | "di" | "iret" | "inc" | "dec"

<op_with_operand> ::= "load" | "store" | "add" | "sub" | "mul" | "div"
                    | "and" | "or" | "jmp" | "jz" | "jn" | "call"
                    | "jc" | "jnc"

<operand> ::= <absolute_operand>
            | <immediate_operand>
            | <indirect_operand>
            | <relative_operand>

<absolute_operand> ::= <number_or_label>

<immediate_operand> ::= "#" <number_or_label>

<indirect_operand> ::= "[" <number_or_label> "]"

<relative_operand>  ::= "@" <identifier>

<number_or_label> ::= <number> | <identifier>

<number> ::= <decimal> | <hexadecimal>
<decimal> ::= ["-"] <digit> { <digit> }
<hexadecimal> ::= "0x" <hex_digit> { <hex_digit> }
<digit> ::= [0-9]
<hex_digit> ::= <digit> | [A-F] | [a-f]

<identifier> ::= <letter> { <letter_or_digit> }
<letter> ::= [A-Z] | [a-z]
<letter_or_digit> ::= <letter> | <digit> | "_"

<any_char_except_quote> ::= любой символ, кроме " и \
```

**Особенности семантики:**
- Строки хранятся в формате C-String (используется директива ```.string```): каждый символ хранится в одном 32-битном слове, конец строки обозначается нуль-терминатором ('\0').
- Директива ```.org``` используется, чтобы размещать код по определенному адресу.
- Директива ```.equ``` используется для определения констант.
- Директива ```.word``` используется для определения 32-битных слов.

## Организация памяти

---

- Архитектура Фон-Неймана
- Размер машинного слова - 32 бита

**Виды адресации:**

| Режим адресации | Синтаксис | Описание |
|------|-------------|----------|
| Immediate | `#imm` | Непосредственная загрузка |
| Absolute | `[addr]` | Прямая адресация |
| Indirect | `[[addr]]` | Косвенная адресация |
| Relative | `@offset` | Относительная адресация |

**Модель памяти:**
- 2 раздельных памяти: память данных и память инструкций
    * Память данных: 32-битные слова
    * Память инструкций: 32-битные слова
- Линейное адресное пространство
- Память данных хранит в себе строки и переменные
- Память инструкций хранит инструкции исполняемого
- Работа с памятью осуществляется с помощью 
- Порты ввода-вывода:
  * ```0xFFFFF0``` - порт ввода
  * ```0xFFFFF1``` - порт вывода (для вывода текста)
  * ```0xFFFFF2``` - регистр ```IE```
  * ```0xFFFFF3``` - адрес обработчика прерываний (по умолчанию ```0x10```)
  * ```0xFFFFF4``` - порт вывода (для вывода чисел)
- Стек: начальный адрес SP - старший адрес памяти данных. Растет в сторону младших адресов памяти.

```
       Instruction memory
+------------------------------+
| 0x00 : .org 0                |
| 0x00 : jmp main              |
| ...                          |
| 0x10 : .org 0x10             | обработчик прерывания
| 0x10 : push                  |
| 0x11 : ...                   |
| ...                          |
| 0x20 : main: load #0         |
| ...                          |
+------------------------------+

       Data memory
+------------------------------+
| 0x0000 : .data               |
| 0x0000 : x: .word 0          | 
| 0x0001 : y: .word 0          |
| 0x0002 : msg: .string "Hi"   | -> 0x0002: 'H', 0x0003: 'i', 0x0004: \0
| ...                          |
| 0xFFFFF0 : input port        |
| 0xFFFFF1 : output port       |
| 0xFFFFF2 : IE register       |
| 0xFFFFF3 : вектор прерывания |
| 0xFFFFF4 : num output port   | 
| ...                          |
+------------------------------+
```

**Регистры:**

| Регистр | Назначение         |
|---------|--------------------|
| PC | Program Counter    |
| ACC | Аккумулятор        |
| SP | Stack Pointer      |
| PS | Флаги Z, N, C, IEF |


## Система команд

---
### Формат инструкции

```
|31..28|27..24|23..0|
|opcode| mode | arg |
```
- **opcode** (4 бита) - код операции
- **mode** (4 бита) - режим адресации
- **arg** (24 бита) - аргумент команды (адрес или непосредственное значение операнда)

### Режимы адресации

| Режим     | Mode |
|-----------|------|
| Absolute  | 0x0  |
| Immediate | 0x1  |
| Indirect  | 0x2  |
| Relative  | 0x3  |

### Набор инструкций

| Инструкция | OPCODE (hex) | MODE (hex) | Операнд | Семантика                                              |
|------------|--------------|------------|---------|--------------------------------------------------------|
| `halt`     | 0x0          | –          | –       | Останов                                                |
| `load`     | 0x1          | *          | `<op>`  | `ACC = <op>`                                           |
| `store`    | 0x2          | *          | `<op>`  | `DataMem[<op>] = ACC`                                  |
| `add`      | 0x3          | *          | `<op>`  | `ACC = ACC + <op>`; обновить `Z, N, C`                 |
| `sub`      | 0x4          | *          | `<op>`  | `ACC = ACC - <op>`; обновить `Z, N, C`                 |
| `mul`      | 0x5          | *          | `<op>`  | `ACC = ACC * <op>`; обновить `Z, N`                    |
| `div`      | 0x6          | *          | `<op>`  | `ACC = ACC // <op>`; обновить `Z, N`                   |
| `and`      | 0x7          | *          | `<op>`  | `ACC = ACC & <op>`; обновить `Z, N`                    |
| `or`       | 0x8          | *          | `<op>`  | `ACC = ACC \| <op>`; обновить `Z, N`                   |
| `not`      | 0x9          | –          | –       | `ACC = ~ACC`; обновить `Z, N`                          |
| `jmp`      | 0xA          | *          | `<op>`  | Безусловный переход                                    |
| `jz`       | 0xB          | *          | `<op>`  | Переход, если `Z == 1`                                 |
| `jn`       | 0xC          | *          | `<op>`  | Переход, если `N == 1`                                 |
| `call`     | 0xD          | *          | `<op>`  | `push(PC+1)`; `PC = <op>`                                  |
| `ret`      | 0xE          | –          | –       | `PC = pop()`                                           |
| `push`     | 0xF          | 0x0        | –       | `push(ACC)`; `SP--`                                    |
| `pop`      | 0xF          | 0x1        | –       | `ACC = pop()`; `SP++`                                  |
| `ei`       | 0xF          | 0x2        | –       | `IEF = 1`                                              |
| `di`       | 0xF          | 0x3        | –       | `IEF = 0`                                              |
| `iret`     | 0xF          | 0x4        | –       | Восстановить `Z,N,C` из стека, `PC = pop()`, `IEF = 1` |
| `inc`      | 0xF          | 0x5        | –       | `ACC = ACC + 1`; обновить `Z, N`                       |
| `dec`      | 0xF          | 0x6        | –       | `ACC = ACC - 1`; обновить `Z, N`                       |
| `jc`       | 0xF          | 0x7        | `<op>`  | Переход, если `C == 1`                                 |
| `jnc`      | 0xF          | 0x8        | `<op>`  | Переход, если `C == 0`                                 |

### Поток управления и прерывания
- Последовательное выполнение: после каждой инструкции ```PC``` увеличивается на 1 (если инструкция не изменяет ```PC``` явно).
- Переходы: ```jmp```, ```jz```, ```jn```, ```jc```, ```jnc``` изменяют ```PC``` на целевой адрес или на ```PC + 1 + смещение```. Конвейер при переходе сбрасывается.
- Вызовы и возвраты: ```call``` сохраняет в стеке адрес возврата, затем выполняет переход. ```ret``` восстанавливает ```PC``` из стека.
- Прерывания:
    * Разрешаются флагом ```IEF```.
    * При наступлении запланированного прерывания процессор сбрасывает ```IEF```, сохраняет в стек ```PC``` и флаги ```Z```, ```N```, ```C```, затем загружает ```PC``` из ячейки ```0xFFFFF3```.
    * Обработчик прерывания должен завершаться инструкцией ```iret```, которая восстанавливает флаги и ```PC``` и устанавливает ```IEF = 1```.
- Останов: инструкция ```halt``` останавливает выполнение.

### Конвейер 

**Реализован конвейер, содержащий 3 стадии:**

| Стадия | Описание |
|----|----------|
| IF | Выборка инструкции из памяти |
| ID | Декодирование, выборка операнда |
| EX | Выполнение операции |

- На каждом такте инструкция продвигается на 1 стадию
- При переходе или обработке прерывания конвейер очищается

## Транслятор

--- 
Интерфейс командной строки: ```python translator.py <source.asm> <target.bin>```

**Аргументы:**
- ```source.asm``` - исходный файл с кодом программы
- ```target.bin``` - путь для сохранения бинарного файла (результат трансляции)

**Выходные файлы:**
- ```<target.bin>``` - бинарный файл (последовательность 32‑битных слов)
- ```<target.bin>.hex``` - текстовый файл в формате ```<address> - <HEX> - <мнемоника>```
- ```<target.bin>.data.json``` - файл в формате JSON, содержит начальные данные (секция ```.data```)

**Транслятор выполняет обработку в 2 прохода:**
- **1-й проход:** Обработка и сохранение меток, сохранение констант (директива ```.equ```), обработка секций (```.data```, ```.text```), создание основы прогаммы
- **2-й проход:** Подстановка числовых адресов вместо меток, констант
После обработки в 2 прохода выполняется запись данных в выходные файлы

## Модель процессора

---
Интерфейс командной строки: ```python machine.py <code.bin> <input_schedule.txt>```

**Аргументы:**
- ```code.bin``` - путь к бинарному файлу с машинным кодом
- ```input_schedule.txt``` - путь к текстовому файлу с с расписанием прерываний (имитация ввода)

Процессор разделен на **Control Unit** и **Data Path**. Поддерживается потактовое исполнение и конвеерная обработка инструкций

## Тестирование

--- 
**Реализованные алгоритмы:**
1. ```cat.asm``` - чтение ввода из порта ```0xFFFFF0``` и вывод в порт ```0xFFFFF1```
2. ```hello.asm``` - вывод текста в порт ```0xFFFFF1```
2. ```hello_user_name.asm``` - запрос имени пользователя, вывод приветствия с соответствующим именем
3. ```sort.asm``` - сортировка массива пузырьком
4. ```double_arith.asm``` - работа числами в 64 бита
5. ```euler6.asm``` - разность квадрата суммы и суммы квадратов

Запуск автоматического тестирования: ```poetry run pytest -v ```

Пример ручного тестирования:
```
> python translator.py examples/cat.asm cat.bin 
> python machine.py cat.bin examples/cat_input.txt

DEBUG:root:TICK:   0 PC:   0 | IF: - | ID: - | EX: - | ACC: 0 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:INTERRUPT at tick 1: char='H'
DEBUG:root:TICK:   1 PC:  16 | IF: - | ID: - | EX: - | ACC: 0 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   2 PC:  17 | IF: LOAD -16 | ID: - | EX: - | ACC: 0 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   3 PC:  18 | IF: JZ 20 | ID: LOAD -16 | EX: - | ACC: 0 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   4 PC:  19 | IF: STORE -15 | ID: JZ 20 | EX: LOAD -16 | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   5 PC:  20 | IF: SPECIAL 0 | ID: STORE -15 | EX: JZ 20 | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:output: '' << 'H'
DEBUG:root:TICK:   6 PC:  21 | IF: HALT 0 | ID: SPECIAL 0 | EX: STORE -15 | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   7 PC:   0 | IF: - | ID: - | EX: SPECIAL 0 | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:INTERRUPT at tick 8: char='\x00'
DEBUG:root:TICK:   8 PC:  16 | IF: - | ID: - | EX: - | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:   9 PC:  17 | IF: LOAD -16 | ID: - | EX: - | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  10 PC:  18 | IF: JZ 20 | ID: LOAD -16 | EX: - | ACC: 72 | PSW: Z=0 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  11 PC:  19 | IF: STORE -15 | ID: JZ 20 | EX: LOAD -16 | ACC: 0 | PSW: Z=1 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  12 PC:  20 | IF: - | ID: - | EX: JZ 20 | ACC: 0 | PSW: Z=1 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  13 PC:  21 | IF: HALT 0 | ID: - | EX: - | ACC: 0 | PSW: Z=1 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  14 PC:  21 | IF: - | ID: HALT 0 | EX: - | ACC: 0 | PSW: Z=1 N=0 C=0 IEF=0 [IRQ]
DEBUG:root:TICK:  15 PC:  21 | IF: - | ID: - | EX: HALT 0 | ACC: 0 | PSW: Z=1 N=0 C=0 IEF=0 [IRQ]
INFO:root:output_buffer: 'H'
H
ticks: 15

```