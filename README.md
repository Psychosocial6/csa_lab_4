# Лабораторная работа №4

- **ФИО:** Зыков Андрей Алексеевич
- **Группа:** P3206
- **Вариант:** asm | acc | harv | hw | tick | binary | trap | mem | cstr | alg2 | ~~pipeline~~

## Язык программирования

---

### Расширенная форма Бэкуса-Наура

```
<program> ::= { <section_data> | <section_text> | <directive_line> | <preprocessor_line> | <empty_or_comment_line> }

<section_data> ::= ".section" ".data" "\n" { <data_line> | <directive_line> | <preprocessor_line> }

<data_line> ::= [ <label_def> ] [ <data_declaration> ] [ <comment> ] "\n"

<data_declaration> ::= <word_directive> | <string_directive>

<word_directive> ::= ".word" <word_list>
<word_list> ::= <number_or_label> { "," <number_or_label> }

<string_directive> ::= ".string" <string_literal>
<string_literal> ::= '"' { <any_char_except_quote> | <escape_seq> } '"'
<escape_seq> ::= "\\n" | "\\t" | "\\\\" | "\\\""

<section_text> ::= ".section" ".text" "\n" { <code_line> | <directive_line> | <preprocessor_line> }

<code_line> ::= [ <label_def> ] [ <statement> ] [ <comment> ] "\n"

<statement> ::= <instruction> | <macro_call>

<directive_line> ::= <directive> [ <comment> ] "\n"
<directive> ::= ".org" <number> | ".equ" <identifier> <number>

<label_def> ::= <identifier> ":"

<instruction> ::= <op_without_operand> | <op_with_operand> <operand>

<macro_call> ::= <identifier>

<op_without_operand> ::= "halt" | "not" | "ret" | "push" | "pop" | "ei" | "di" | "iret" | "inc" | "dec" | "nop"

<op_with_operand> ::= "load" | "store" | "add" | "sub" | "and" | "or" | "jmp" | "jz" | "jn" | "call" | "jc" | "jnc"

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

<digit> ::= "0" ... "9"
<hex_digit> ::= <digit> | "a" ... "f" | "A" ... "F"

<identifier> ::= <letter> { <letter_or_digit> }
<letter> ::= "a" ... "z" | "A" ... "Z"
<letter_or_digit> ::= <letter> | <digit> | "_"

<comment> ::= ";" { <any_character_except_newline> }
<empty_or_comment_line> ::= [ <comment> ] "\n"

<preprocessor_line> ::= <preprocessor_directive> [ <comment> ] "\n"
<preprocessor_directive> ::= <macro_directive> | <cond_directive>
<macro_directive> ::= ".macro" <identifier> | ".endmacro"
<cond_directive>  ::= ".if" <identifier> | ".else" | ".endif"

<any_char_except_quote> ::= ? любой символ, кроме " и \ ?
<any_character_except_newline> ::= ? любой символ, кроме символа новой строки ?
```

### Описание семантики

- **Стратегия вычислений:** строгая стратегия вычислений, аргументы всегда вычисляются полностью до применения функции к ним. Присутствует **вызов по значению** (для непосредственной загрузки) и **вызов по сслыке** (для остальных видов адресации)
- **Области видимости:** глобальная область видимости, все метки, объявленные в секциях `.data` и `.text`, имеют глобальную область видимости, наличие двух одинаковых меток недопустимо. Аналогично глобальную область видимости имеют константы. На концептуальном уровне локальную видимость имеют переменные в стеке, так как актуальны в рамках текущей подпрограммы и недоступны при обращении по имени (не имеют меток). На физическом уровне переменную из стека все равно возможно получить через обращение по прямому адресу в памяти.
- **Типизация:** строгая типизация как таковая отсутствует, интерпретация машинного слова зависит от выполняемой над ним инструкции.
- **Виды литералов:** 
  * **Десятичные целочисленные:** знаковые целые числа в десятичной системе счисления (`10`, `-4`).
  * **Шестнадцатеричные целочисленные:** числа в шестнадцатеричной системе счисления, могут быть интерпретированы как знаковые и как беззнаковые. Начинаются с префикса `0x` (`0xFFFFFFFF`, `0x1FFFABC`)
  * **Строковые литералы:** представляют собой последовательности символов, заключенные в двойные кавычки (`"Hello"`, `"World!\n"`). Хранятся в формате C-String: последовательность символов оканчивается нуль-терминатором. Для хранения одного символа выделяется одно 32-битное машинное слово.
- **Пользовательские макроопределения:**
  * **Константы:** объявляются с помощью директивы `.equ`. Могут использоваться как операнды команд, не занимают памяти, так как все используемые значения заменяются транслятором на непосредственное значение.
  * **Макросы:** начинаются и заканчиваются директивами `.macro <identifier>` и `.endmacro`, соответственно. Тело макроса содержит некоторое количество инструкций, при трансляции все имена макросов заменяются на последовательность инструкций, определенную в их теле.
  * **Условная компиляция:** условно компилируемые фрагменты определяются тремя директивами: `.if <identifier>`, `.else`, `.endif`. В качестве условия (`<identifier>`) проверяется значение константы, определенной директивой `.equ`. Если значение константы равно 0 или константа не определена, код в теле `.if` игнорируется. Директива `.else` является опциональной и компилируется, если не было выполнено условие `.if`. Директива `.endif` показывает окончание блока условной компиляции


## Организация памяти

---

### Модель памяти

Гарвардская архитектура: 2 раздельных памяти для данных и для инструкций. Используются 32-битные машинные слова. Присутствуют несколько видов адресации: прямая, косвенная, относительная, непосредственная загрузка операнда.
- **Память данных:** размер 1024 ячейки. Хранит переменные, строки, стек.
- **Память команд:** размер 2^24 (адреса с `0x0` до `0xFFFFFF`), доступна только для чтения. Хранит инструкции.

Минимальная единица данных - машинное слово

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
| 0x03FF : SP                  | начало стека
| ...                          |
| 0xFFFFF0 : input port        |
| 0xFFFFF1 : output port       |
| 0xFFFFF2 : num output port   |
| 0xFFFFF3 : вектор прерывания |
+------------------------------+
```

- Порты ввода-вывода:
  * ```0xFFFFF0``` - порт ввода
  * ```0xFFFFF1``` - порт вывода (для вывода текста)
  * ```0xFFFFF2``` - порт вывода (для вывода чисел)
  * ```0xFFFFF3``` - вектор прерываний (по умолчанию ```0x10```)

### Регистры

| Регистр | Назначение         |
|---------|--------------------|
| PC      | Program Counter    |
| ACC     | Аккумулятор        |
| SP      | Stack Pointer      |
| PS      | Флаги Z, N, C, IEF |

### Флаги

| Флаг | Назначение                  |
|------|-----------------------------|
| Z    | Результат равен 0           |
| N    | Отрицательный результат     |
| C    | Перенос из старшего разряда |
| IEF  | Разрешены прерывания        |


### Виды адресации

| Режим адресации | Синтаксис  | Описание                  |
|-----------------|------------|---------------------------|
| Immediate       | `#imm`     | Непосредственная загрузка |
| Absolute        | `[addr]`   | Прямая адресация          |
| Indirect        | `[[addr]]` | Косвенная адресация       |
| Relative        | `@offset`  | Относительная адресация   |

### Размещение в памяти

- **Литералы:**
  * Литералы, укладывающиеся в 24 бита могут кодироваться непосредственно внутри самой инструкции при использовании режима непосредственной адресации `#imm` (`LOAD #10`, `ADD #1`). Не занимают места в памяти данных.
  * Числа, занимающие 32 бита или инициализирующиеся в секции `.data` занимают одну 32-битную ячейку памяти данных.
  * Символьные литералы преобразуются транслятором в целочисленные ASCII-коды и обрабатываются процессором как обычные числа.
  * Строковые литералы размещаются в памяти данных в формате C-String, каждый символ занимает одно машинное слово (младший байт).

- **Константы:**
  * Константы, объявленные через директиву `.equ` преобразуются на этапе трансляции и их текстовые имена заменяются числовыми значениями.

- **Переменные:**
  * Все переменные отображаются на память данных, начиная с адреса `0x0` (или с адреса, заданного директивой `.org`). 
  
- **Инструкции:**
  * Размещаются последовательно в памяти с инструкций, начиная с адреса `0x0` (или с адреса, заданного директивой `.org`). Все метки окончательно разрешаются на 2-м проходе транслятора.
  * Начало программы указывает метка `start:`, при ее отсутствии программа начинается с адреса `0x0`

- **Процедуры:**
  * Все процедуры размещаются в памяти команд.
  * Вызов процедуры выполняется инструкцией `CALL` при этом значение `PC + 1` сохраняется в стек, а в `PC` записывается адрес начала подпрограммы.
  * Возврат из процедуры выполняется инструкцией `RET`, адрес возврата извлекается из стека и записывается в `PC`.
  * Изначально `SP` указывает на последнюю ячейку памяти, при добавлении в стек `SP` уменьшается на 1.

- **Прерывания:**
  * Обработчик прерываний располагается по адресу, указанному в векторе прерывания (`0x10`), в памяти инструкций.
  * При наступлении прерывания процессор сохраняет в стек `PC`, сохраняет флаги `Z, N, C`, устанавливает `IEF = 0` (для защиты от вложенных прерываний), читает вектор прерывания и устанавливает в `PC` адрес обработчика.
  * Для возврата из прерывания используется инструкция `IRET`. При использовании инструкции значения флагов `Z, N, C` и регистра `PC` восстанавливаются, извлекаясь из стека, флаг `IEF` устанавливается равным 1.

## Система команд

---
### Особенности процессора

- Аккумуляторная архитектура, работа строится вокруг специализированного регистра (`ACC`), куда сохраняется результат большинства операций
- Нет как таковой строгой типизации, значения могут интерпретироваться по-разному
- Гарвардская архитектура: память данных и память инструкций. Представлены несколько видов адресации
- Реализован Memory-Mapped IO. Ввод осуществляется по прерываниям
- Присутствуют инструкции управления потоком выполнения (различные виды переходов), инструкции для работы с прерываниями

### Формат инструкции

```
|31..28|27..24|23..0|
|opcode| mode | arg |
```
- **opcode** (4 бита) - код операции
- **mode** (4 бита) - режим адресации
- **arg** (24 бита) - аргумент инструкции (адрес или непосредственное значение операнда)

### Режимы адресации

| Режим     | Mode | Сокращение |
|-----------|------|------------|
| Absolute  | 0x0  | Abs        |
| Immediate | 0x1  | Imm        |
| Indirect  | 0x2  | Ind        |
| Relative  | 0x3  | Rel        |

Во всех командах с кодом операции `0x0` биты режима адресации используются как часть кода операции.

### Набор инструкций

| Инструкция | OPCODE (hex) | MODE (hex) | Полный цикл исполнения (тактов) | Режимы адресации    | Операнд | Семантика                                              |
|------------|--------------|------------|---------------------------------|---------------------|---------|--------------------------------------------------------|
| `NOP`      | `0x0`        | `0x0`      | 2                               | –                   | –       | Нет операции                                           | 
| `LOAD`     | `0x1`        | *          | 5(Abs), 4(Imm), 7(Ind)          | `Abs`, `Imm`, `Ind` | `<op>`  | `ACC = <op>`                                           |
| `STORE`    | `0x2`        | *          | 4(Abs), 7(Ind)                  | `Abs`, `Ind`        | `<op>`  | `DataMemory[<op>] = ACC`                               |
| `ADD`      | `0x3`        | *          | 5(Abs), 4(Imm), 7(Ind)          | `Abs`, `Imm`, `Ind` | `<op>`  | `ACC = ACC + <op>`; set `Z, N, C`                      |
| `SUB`      | `0x4`        | *          | 5(Abs), 4(Imm), 7(Ind)          | `Abs`, `Imm`, `Ind` | `<op>`  | `ACC = ACC - <op>`; set `Z, N, C`                      |
| `AND`      | `0x5`        | *          | 5(Abs), 4(Imm), 7(Ind)          | `Abs`, `Imm`, `Ind` | `<op>`  | `ACC = ACC & <op>`; set `Z, N`                         |
| `OR`       | `0x6`        | *          | 5(Abs), 4(Imm), 7(Ind)          | `Abs`, `Imm`, `Ind` | `<op>`  | `ACC = ACC \| <op>`; set `Z, N`                        |
| `JMP`      | `0x7`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PC = <op>`                                            |
| `JZ`       | `0x8`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PC = <op>`, если `Z == 1`                             |
| `JN`       | `0x9`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PC = <op>`, если `N == 1`                             |
| `JC`       | `0xA`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PC = <op>`, если `C == 1`                             |
| `JNC`      | `0xB`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PC = <op>`, если `C == 0`                             |
| `CALL`     | `0xC`        | *          | 3(Abs), 3(Rel)                  | `Abs`, `Rel`        | `<op>`  | `PUSH(PC+1)`; `PC = <op>`                              |
| `PUSH`     | `0xD`        | –          | 4                               | –                   | –       | `DataMemory[SP] = ACC`; `SP--`                         |
| `POP`      | `0xE`        | –          | 5                               | –                   | –       | `ACC = DataMemory[SP]; SP++`                           |
| `EI`       | `0xF`        | `0x0`      | 3                               | –                   | –       | `IEF = 1`                                              |
| `DI`       | `0xF`        | `0x1`      | 3                               | –                   | –       | `IEF = 0`                                              |
| `IRET`     | `0xF`        | `0x2`      | 7                               | –                   | –       | Восстановить `Z,N,C` из стека, `PC = POP()`, `IEF = 1` |
| `INC`      | `0xF`        | `0x3`      | 3                               | –                   | –       | `ACC = ACC + 1`; обновить `Z, N`                       |
| `DEC`      | `0xF`        | `0x4`      | 3                               | –                   | –       | `ACC = ACC - 1`; обновить `Z, N`                       |
| `NOT`      | `0xF`        | `0x5`      | 3                               | –                   | –       | `ACC = ~ACC`; set `Z, N`                               |
| `RET`      | `0xF`        | `0x6`      | 5                               | –                   | –       | `PC = DataMemory[SP]`                                  |
| `HALT`     | `0xF`        | `0x7`      | 2                               | –                   | –       | Останов выполнения                                     |

### Поток управления и прерывания
- Последовательное выполнение: после каждой инструкции ```PC``` увеличивается на 1 (если инструкция не изменяет ```PC``` явно).
- Переходы: ```JMP```, ```JZ```, ```JN```, ```JC```, ```JNC``` изменяют ```PC``` на целевой адрес или на ```PC + 1 + смещение```.
- Вызовы и возвраты: ```CALL``` сохраняет в стеке адрес возврата, затем выполняет переход на указанный адрес подпрограммы. ```RET``` восстанавливает ```PC``` из стека.
- Прерывания:
    * Разрешаются флагом ```IEF```.
    * При наступлении прерывания процессор сбрасывает ```IEF``` (для запрета вложенных прерываний), сохраняет в стек ```PC``` и флаги ```Z, N, C```, затем устанавливает новое значение `PC`, полученное из вектора прерывания.
    * Обработчик прерывания должен завершаться инструкцией ```IRET```, которая восстанавливает флаги и ```PC``` и устанавливает ```IEF = 1```.
- Останов: инструкция ```HALT``` останавливает выполнение.

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

**Транслятор выполняет обработку в 3 прохода:**
- **1-й проход:** Препроцессинг. Во время прохода осуществляется сбор значений констант `.equ` для использования в блоках условной компиляции, все вызовы макросов заменяются инструкциями, определенными в их теле, обрабатывается условная компиляция, все неиспользуемые строки удаляются 
- **2-й проход:** Обработка и сохранение меток, сохранение констант (директива ```.equ```), обработка секций (```.data```, ```.text```), создание основы программы
- **3-й проход:** Подстановка числовых адресов вместо меток, констант
После обработки в 3 прохода выполняется запись данных в выходные файлы

## Модель процессора

---
Интерфейс командной строки: ```python machine.py <code.bin> <input_schedule.txt>```

**Аргументы:**
- ```code.bin``` - путь к бинарному файлу с машинным кодом
- ```input_schedule.txt``` - путь к текстовому файлу с с расписанием прерываний

Процессор разделен на **Control Unit** и **Data Path**.

### Control Unit

![Control Unit](shemes/ControlUnit.png)

**Описание регистров:**
- **PC:** указатель исполняемой инструкции
- **IR:** регистр для сохранения инструкции, извлеченной из памяти инструкций

**Описание управляющих сигналов:**
- **latch_IR, latch_PC:** управляюшие синалы, защелкиваюшие значения в соответствующих регистрах
- **sel_PC:** управляющий сигнал мультиплексора перед `PC`, осуществляет выбор нового значения `PC`: значение из DataPath (регистр DR) - адрес из стека или вектор прерывания; `PC+offset` - адрес при относительной адресации; `Absolute_addr` - адрес при абсолютной адресации.
- **Signals:** управляющие сигналы для элементов DataPath

### Data Path

![Data Path](shemes/DataPath.png)

**Описание регистров:**
- **DR:** регистр данных, промежуточный регистр для работы с памятью, хранит выбранный операнд
- **SP:** указатель стека, содержит адрес вершины стека
- **AR:** регистр адреса, хранит адрес ячейки Data Memory, к которой осуществляется обращение
- **ACC:** аккумулятор, хранит результаты выполнения инструкций
- **N,Z,C,IEF (SR):**  регистр состояния, хранит флаги 
- **INT_VEC:** хранит вектор прерывания

**Описание управляющих сигналов:**
- **latch_DR, latch_SP, latch_AR, latch_ACC, latch_flags:** управляюшие сигналы, защелкиваюшие значения в соответствующих регистрах
- **sel_OP:** управляющий сигнал мультиплексора правого входа АЛУ, осуществляет выбор операнда: +1, -1 (для операций `INC`, `DEC`) или значение из регистра `DR`
- **sel_operation:** управляющий сигнал АЛУ, отвечает за выбор выполняемой операции
- **sel_SP:** управляющий сигнал мультиплексора перед `SP`, осуществляет выбор нового значения `SP`: `SP+1` или `SP-1`
- **sel_AR:** управляющий сигнал мультиплексора перед `AR`, осуществляет выбор нового значения `AR`: Абсолютный адрес из исполняемой инструкции, адрес вершины стека (из `SP`) или адрес из `DR`, извлеченный из памяти при косвенной адресации
- **sel_DR:** управляющий сигнал мультиплексора перед `DR`, осуществляет выбор нового значения `DR`: Значение из аккумулятора (для сохранения в память), значение `SR` (флагов) (для сохранения в стек перед обработкой прерывания), значение, поступившее на ввод с внешнего устройства, значение `PC` (для сохранения в стек перед обработкой прерывания или переходом к подпрограмме), значение из исполняемой инструкции (при непосредственной загрузке операнда), значение, извлеченное из памяти (при выборке операнда или при выборке адреса при косвенной адресации)
- **ACD_SEL:** управляющий сигнал из дешифратора адреса для Data Memory, `INT_VEC` и интерфейсов внешних устройств для осуществления вывода в выбранное устройство

**Описание флагов:**
- **N:** флаг, указывающий, что результат операции в АЛУ - отрицательное число
- **Z:** флаг, указывающий, что результат операции в АЛУ равен 0
- **C:** флаг, указывающий, что при выполнении операции в АЛУ произошел перенос из старшего разряда
- **IEF(Interrupt Enable Flag):** флаг, указывающий, разрешены ли в данный момент прерывания

## Тестирование

--- 
**Реализованные алгоритмы:**
1. ```cat.asm``` - чтение ввода из порта ```0xFFFFF0``` и вывод в порт ```0xFFFFF1```
2. ```hello.asm``` - вывод текста в порт ```0xFFFFF1```
3. ```hello_user_name.asm``` - запрос имени пользователя, вывод приветствия с соответствующим именем
4. ```sort.asm``` - сортировка массива пузырьком
5. ```double_arith.asm``` - работа числами в 64 бита
6. ```euler6.asm``` - разность квадрата суммы и суммы квадратов
7. 

Запуск автоматического тестирования: ```poetry run pytest -v ```

Пример ручного тестирования:
```
> python translator.py examples/hello.asm hello.bin 
> python machine.py hello.bin

DEBUG:root:TICK:   0 PC:   0 | INSTR: -            | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   1 PC:   1 | INSTR: load 0       | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   2 PC:   1 | INSTR: load 0       | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   3 PC:   1 | INSTR: load 0       | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   4 PC:   1 | INSTR: load 0       | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   5 PC:   3 | INSTR: call 0x03    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   6 PC:   3 | INSTR: call 0x03    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   7 PC:   3 | INSTR: call 0x03    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   8 PC:   4 | INSTR: store 0x0F   | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:   9 PC:   4 | INSTR: store 0x0F   | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  10 PC:   4 | INSTR: store 0x0F   | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  11 PC:   4 | INSTR: store 0x0F   | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  12 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  13 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  14 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  15 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  16 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  17 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  18 PC:   5 | INSTR: load 0x0F    | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  19 PC:   6 | INSTR: jz 0x0B      | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  20 PC:   6 | INSTR: jz 0x0B      | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  21 PC:   6 | INSTR: jz 0x0B      | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: '' << 'H'
DEBUG:root:TICK:  22 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  23 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  24 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  25 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    72 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  26 PC:   8 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  27 PC:   8 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  28 PC:   8 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  29 PC:   8 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  30 PC:   8 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK:  31 PC:   9 | INSTR: inc          | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  32 PC:   9 | INSTR: inc          | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  33 PC:   9 | INSTR: inc          | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  34 PC:  10 | INSTR: store 0x0F   | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  35 PC:  10 | INSTR: store 0x0F   | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  36 PC:  10 | INSTR: store 0x0F   | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  37 PC:  10 | INSTR: store 0x0F   | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  38 PC:   4 | INSTR: jmp 0x04     | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  39 PC:   4 | INSTR: jmp 0x04     | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  40 PC:   4 | INSTR: jmp 0x04     | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  41 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  42 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  43 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  44 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  45 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  46 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  47 PC:   5 | INSTR: load 0x0F    | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  48 PC:   6 | INSTR: jz 0x0B      | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  49 PC:   6 | INSTR: jz 0x0B      | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  50 PC:   6 | INSTR: jz 0x0B      | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'H' << 'e'
DEBUG:root:TICK:  51 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  52 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  53 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  54 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   101 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  55 PC:   8 | INSTR: load 0x0F    | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  56 PC:   8 | INSTR: load 0x0F    | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  57 PC:   8 | INSTR: load 0x0F    | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  58 PC:   8 | INSTR: load 0x0F    | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  59 PC:   8 | INSTR: load 0x0F    | ACC:     1 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  60 PC:   9 | INSTR: inc          | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  61 PC:   9 | INSTR: inc          | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  62 PC:   9 | INSTR: inc          | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  63 PC:  10 | INSTR: store 0x0F   | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  64 PC:  10 | INSTR: store 0x0F   | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  65 PC:  10 | INSTR: store 0x0F   | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  66 PC:  10 | INSTR: store 0x0F   | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  67 PC:   4 | INSTR: jmp 0x04     | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  68 PC:   4 | INSTR: jmp 0x04     | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  69 PC:   4 | INSTR: jmp 0x04     | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  70 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  71 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  72 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  73 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  74 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  75 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  76 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  77 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  78 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  79 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'He' << 'l'
DEBUG:root:TICK:  80 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  81 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  82 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  83 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  84 PC:   8 | INSTR: load 0x0F    | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  85 PC:   8 | INSTR: load 0x0F    | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  86 PC:   8 | INSTR: load 0x0F    | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  87 PC:   8 | INSTR: load 0x0F    | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  88 PC:   8 | INSTR: load 0x0F    | ACC:     2 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  89 PC:   9 | INSTR: inc          | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  90 PC:   9 | INSTR: inc          | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  91 PC:   9 | INSTR: inc          | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  92 PC:  10 | INSTR: store 0x0F   | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  93 PC:  10 | INSTR: store 0x0F   | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  94 PC:  10 | INSTR: store 0x0F   | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  95 PC:  10 | INSTR: store 0x0F   | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  96 PC:   4 | INSTR: jmp 0x04     | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  97 PC:   4 | INSTR: jmp 0x04     | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  98 PC:   4 | INSTR: jmp 0x04     | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK:  99 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 100 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 101 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 102 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 103 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 104 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 105 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 106 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 107 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 108 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hel' << 'l'
DEBUG:root:TICK: 109 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 110 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 111 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 112 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 113 PC:   8 | INSTR: load 0x0F    | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 114 PC:   8 | INSTR: load 0x0F    | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 115 PC:   8 | INSTR: load 0x0F    | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 116 PC:   8 | INSTR: load 0x0F    | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 117 PC:   8 | INSTR: load 0x0F    | ACC:     3 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 118 PC:   9 | INSTR: inc          | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 119 PC:   9 | INSTR: inc          | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 120 PC:   9 | INSTR: inc          | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 121 PC:  10 | INSTR: store 0x0F   | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 122 PC:  10 | INSTR: store 0x0F   | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 123 PC:  10 | INSTR: store 0x0F   | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 124 PC:  10 | INSTR: store 0x0F   | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 125 PC:   4 | INSTR: jmp 0x04     | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 126 PC:   4 | INSTR: jmp 0x04     | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 127 PC:   4 | INSTR: jmp 0x04     | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 128 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 129 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 130 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 131 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 132 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 133 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 134 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 135 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 136 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 137 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hell' << 'o'
DEBUG:root:TICK: 138 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 139 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 140 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 141 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 142 PC:   8 | INSTR: load 0x0F    | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 143 PC:   8 | INSTR: load 0x0F    | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 144 PC:   8 | INSTR: load 0x0F    | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 145 PC:   8 | INSTR: load 0x0F    | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 146 PC:   8 | INSTR: load 0x0F    | ACC:     4 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 147 PC:   9 | INSTR: inc          | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 148 PC:   9 | INSTR: inc          | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 149 PC:   9 | INSTR: inc          | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 150 PC:  10 | INSTR: store 0x0F   | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 151 PC:  10 | INSTR: store 0x0F   | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 152 PC:  10 | INSTR: store 0x0F   | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 153 PC:  10 | INSTR: store 0x0F   | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 154 PC:   4 | INSTR: jmp 0x04     | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 155 PC:   4 | INSTR: jmp 0x04     | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 156 PC:   4 | INSTR: jmp 0x04     | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 157 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 158 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 159 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 160 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 161 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 162 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 163 PC:   5 | INSTR: load 0x0F    | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 164 PC:   6 | INSTR: jz 0x0B      | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 165 PC:   6 | INSTR: jz 0x0B      | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 166 PC:   6 | INSTR: jz 0x0B      | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello' << ','
DEBUG:root:TICK: 167 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 168 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 169 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 170 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    44 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 171 PC:   8 | INSTR: load 0x0F    | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 172 PC:   8 | INSTR: load 0x0F    | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 173 PC:   8 | INSTR: load 0x0F    | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 174 PC:   8 | INSTR: load 0x0F    | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 175 PC:   8 | INSTR: load 0x0F    | ACC:     5 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 176 PC:   9 | INSTR: inc          | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 177 PC:   9 | INSTR: inc          | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 178 PC:   9 | INSTR: inc          | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 179 PC:  10 | INSTR: store 0x0F   | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 180 PC:  10 | INSTR: store 0x0F   | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 181 PC:  10 | INSTR: store 0x0F   | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 182 PC:  10 | INSTR: store 0x0F   | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 183 PC:   4 | INSTR: jmp 0x04     | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 184 PC:   4 | INSTR: jmp 0x04     | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 185 PC:   4 | INSTR: jmp 0x04     | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 186 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 187 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 188 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 189 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 190 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 191 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 192 PC:   5 | INSTR: load 0x0F    | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 193 PC:   6 | INSTR: jz 0x0B      | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 194 PC:   6 | INSTR: jz 0x0B      | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 195 PC:   6 | INSTR: jz 0x0B      | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello,' << ' '
DEBUG:root:TICK: 196 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 197 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 198 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 199 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    32 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 200 PC:   8 | INSTR: load 0x0F    | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 201 PC:   8 | INSTR: load 0x0F    | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 202 PC:   8 | INSTR: load 0x0F    | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 203 PC:   8 | INSTR: load 0x0F    | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 204 PC:   8 | INSTR: load 0x0F    | ACC:     6 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 205 PC:   9 | INSTR: inc          | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 206 PC:   9 | INSTR: inc          | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 207 PC:   9 | INSTR: inc          | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 208 PC:  10 | INSTR: store 0x0F   | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 209 PC:  10 | INSTR: store 0x0F   | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 210 PC:  10 | INSTR: store 0x0F   | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 211 PC:  10 | INSTR: store 0x0F   | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 212 PC:   4 | INSTR: jmp 0x04     | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 213 PC:   4 | INSTR: jmp 0x04     | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 214 PC:   4 | INSTR: jmp 0x04     | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 215 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 216 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 217 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 218 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 219 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 220 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 221 PC:   5 | INSTR: load 0x0F    | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 222 PC:   6 | INSTR: jz 0x0B      | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 223 PC:   6 | INSTR: jz 0x0B      | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 224 PC:   6 | INSTR: jz 0x0B      | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, ' << 'W'
DEBUG:root:TICK: 225 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 226 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 227 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 228 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    87 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 229 PC:   8 | INSTR: load 0x0F    | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 230 PC:   8 | INSTR: load 0x0F    | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 231 PC:   8 | INSTR: load 0x0F    | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 232 PC:   8 | INSTR: load 0x0F    | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 233 PC:   8 | INSTR: load 0x0F    | ACC:     7 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 234 PC:   9 | INSTR: inc          | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 235 PC:   9 | INSTR: inc          | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 236 PC:   9 | INSTR: inc          | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 237 PC:  10 | INSTR: store 0x0F   | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 238 PC:  10 | INSTR: store 0x0F   | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 239 PC:  10 | INSTR: store 0x0F   | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 240 PC:  10 | INSTR: store 0x0F   | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 241 PC:   4 | INSTR: jmp 0x04     | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 242 PC:   4 | INSTR: jmp 0x04     | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 243 PC:   4 | INSTR: jmp 0x04     | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 244 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 245 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 246 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 247 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 248 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 249 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 250 PC:   5 | INSTR: load 0x0F    | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 251 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 252 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 253 PC:   6 | INSTR: jz 0x0B      | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, W' << 'o'
DEBUG:root:TICK: 254 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 255 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 256 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 257 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   111 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 258 PC:   8 | INSTR: load 0x0F    | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 259 PC:   8 | INSTR: load 0x0F    | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 260 PC:   8 | INSTR: load 0x0F    | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 261 PC:   8 | INSTR: load 0x0F    | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 262 PC:   8 | INSTR: load 0x0F    | ACC:     8 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 263 PC:   9 | INSTR: inc          | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 264 PC:   9 | INSTR: inc          | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 265 PC:   9 | INSTR: inc          | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 266 PC:  10 | INSTR: store 0x0F   | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 267 PC:  10 | INSTR: store 0x0F   | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 268 PC:  10 | INSTR: store 0x0F   | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 269 PC:  10 | INSTR: store 0x0F   | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 270 PC:   4 | INSTR: jmp 0x04     | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 271 PC:   4 | INSTR: jmp 0x04     | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 272 PC:   4 | INSTR: jmp 0x04     | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 273 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 274 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 275 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 276 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 277 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 278 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 279 PC:   5 | INSTR: load 0x0F    | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 280 PC:   6 | INSTR: jz 0x0B      | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 281 PC:   6 | INSTR: jz 0x0B      | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 282 PC:   6 | INSTR: jz 0x0B      | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, Wo' << 'r'
DEBUG:root:TICK: 283 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 284 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 285 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 286 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   114 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 287 PC:   8 | INSTR: load 0x0F    | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 288 PC:   8 | INSTR: load 0x0F    | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 289 PC:   8 | INSTR: load 0x0F    | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 290 PC:   8 | INSTR: load 0x0F    | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 291 PC:   8 | INSTR: load 0x0F    | ACC:     9 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 292 PC:   9 | INSTR: inc          | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 293 PC:   9 | INSTR: inc          | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 294 PC:   9 | INSTR: inc          | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 295 PC:  10 | INSTR: store 0x0F   | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 296 PC:  10 | INSTR: store 0x0F   | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 297 PC:  10 | INSTR: store 0x0F   | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 298 PC:  10 | INSTR: store 0x0F   | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 299 PC:   4 | INSTR: jmp 0x04     | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 300 PC:   4 | INSTR: jmp 0x04     | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 301 PC:   4 | INSTR: jmp 0x04     | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 302 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 303 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 304 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 305 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 306 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 307 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 308 PC:   5 | INSTR: load 0x0F    | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 309 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 310 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 311 PC:   6 | INSTR: jz 0x0B      | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, Wor' << 'l'
DEBUG:root:TICK: 312 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 313 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 314 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 315 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   108 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 316 PC:   8 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 317 PC:   8 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 318 PC:   8 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 319 PC:   8 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 320 PC:   8 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 321 PC:   9 | INSTR: inc          | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 322 PC:   9 | INSTR: inc          | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 323 PC:   9 | INSTR: inc          | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 324 PC:  10 | INSTR: store 0x0F   | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 325 PC:  10 | INSTR: store 0x0F   | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 326 PC:  10 | INSTR: store 0x0F   | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 327 PC:  10 | INSTR: store 0x0F   | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 328 PC:   4 | INSTR: jmp 0x04     | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 329 PC:   4 | INSTR: jmp 0x04     | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 330 PC:   4 | INSTR: jmp 0x04     | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 331 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 332 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 333 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 334 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 335 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 336 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 337 PC:   5 | INSTR: load 0x0F    | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 338 PC:   6 | INSTR: jz 0x0B      | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 339 PC:   6 | INSTR: jz 0x0B      | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 340 PC:   6 | INSTR: jz 0x0B      | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, Worl' << 'd'
DEBUG:root:TICK: 341 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 342 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 343 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 344 PC:   7 | INSTR: store 0xFFFFF1 | ACC:   100 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 345 PC:   8 | INSTR: load 0x0F    | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 346 PC:   8 | INSTR: load 0x0F    | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 347 PC:   8 | INSTR: load 0x0F    | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 348 PC:   8 | INSTR: load 0x0F    | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 349 PC:   8 | INSTR: load 0x0F    | ACC:    11 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 350 PC:   9 | INSTR: inc          | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 351 PC:   9 | INSTR: inc          | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 352 PC:   9 | INSTR: inc          | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 353 PC:  10 | INSTR: store 0x0F   | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 354 PC:  10 | INSTR: store 0x0F   | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 355 PC:  10 | INSTR: store 0x0F   | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 356 PC:  10 | INSTR: store 0x0F   | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 357 PC:   4 | INSTR: jmp 0x04     | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 358 PC:   4 | INSTR: jmp 0x04     | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 359 PC:   4 | INSTR: jmp 0x04     | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 360 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 361 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 362 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 363 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 364 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 365 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 366 PC:   5 | INSTR: load 0x0F    | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 367 PC:   6 | INSTR: jz 0x0B      | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 368 PC:   6 | INSTR: jz 0x0B      | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 369 PC:   6 | INSTR: jz 0x0B      | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, World' << '!'
DEBUG:root:TICK: 370 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 371 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 372 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 373 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    33 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 374 PC:   8 | INSTR: load 0x0F    | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 375 PC:   8 | INSTR: load 0x0F    | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 376 PC:   8 | INSTR: load 0x0F    | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 377 PC:   8 | INSTR: load 0x0F    | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 378 PC:   8 | INSTR: load 0x0F    | ACC:    12 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 379 PC:   9 | INSTR: inc          | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 380 PC:   9 | INSTR: inc          | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 381 PC:   9 | INSTR: inc          | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 382 PC:  10 | INSTR: store 0x0F   | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 383 PC:  10 | INSTR: store 0x0F   | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 384 PC:  10 | INSTR: store 0x0F   | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 385 PC:  10 | INSTR: store 0x0F   | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 386 PC:   4 | INSTR: jmp 0x04     | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 387 PC:   4 | INSTR: jmp 0x04     | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 388 PC:   4 | INSTR: jmp 0x04     | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 389 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 390 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 391 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 392 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 393 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 394 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 395 PC:   5 | INSTR: load 0x0F    | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 396 PC:   6 | INSTR: jz 0x0B      | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 397 PC:   6 | INSTR: jz 0x0B      | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 398 PC:   6 | INSTR: jz 0x0B      | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:output: 'Hello, World!' << '\n'
DEBUG:root:TICK: 399 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 400 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 401 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 402 PC:   7 | INSTR: store 0xFFFFF1 | ACC:    10 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 403 PC:   8 | INSTR: load 0x0F    | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 404 PC:   8 | INSTR: load 0x0F    | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 405 PC:   8 | INSTR: load 0x0F    | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 406 PC:   8 | INSTR: load 0x0F    | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 407 PC:   8 | INSTR: load 0x0F    | ACC:    13 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 408 PC:   9 | INSTR: inc          | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 409 PC:   9 | INSTR: inc          | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 410 PC:   9 | INSTR: inc          | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 411 PC:  10 | INSTR: store 0x0F   | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 412 PC:  10 | INSTR: store 0x0F   | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 413 PC:  10 | INSTR: store 0x0F   | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 414 PC:  10 | INSTR: store 0x0F   | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 415 PC:   4 | INSTR: jmp 0x04     | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 416 PC:   4 | INSTR: jmp 0x04     | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 417 PC:   4 | INSTR: jmp 0x04     | ACC:    14 | PSW: Z=0 N=0 C=0 IEF=1
DEBUG:root:TICK: 418 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 419 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 420 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 421 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 422 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 423 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 424 PC:   5 | INSTR: load 0x0F    | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 425 PC:  11 | INSTR: jz 0x0B      | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 426 PC:  11 | INSTR: jz 0x0B      | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 427 PC:  11 | INSTR: jz 0x0B      | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 428 PC:   2 | INSTR: ret          | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 429 PC:   2 | INSTR: ret          | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 430 PC:   2 | INSTR: ret          | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 431 PC:   2 | INSTR: ret          | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 432 PC:   2 | INSTR: ret          | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 433 PC:   3 | INSTR: halt         | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
DEBUG:root:TICK: 434 PC:   3 | INSTR: halt         | ACC:     0 | PSW: Z=1 N=0 C=0 IEF=1
INFO:root:output_buffer: 'Hello, World!\n'
Hello, World!

ticks: 434
```