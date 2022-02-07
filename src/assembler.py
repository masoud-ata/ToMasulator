import re
from typing import List

from instruction import Instruction


def assemble(raw_code=""):
    success = True
    offending_line = 0
    instructions: List[Instruction] = []

    lines = raw_code.split("\n")
    for line_num, line in enumerate(lines):
        tokens = __tokenize(line)
        is_empty_line = not tokens
        if is_empty_line:
            continue
        if __is_valid(tokens):
            inst = __make_instruction_from(line, tokens)
            instructions.append(inst)
        else:
            success = False
            offending_line = line_num + 1
            break
    return success, offending_line, instructions


def __tokenize(line):
    tokens = re.findall(r"(\w+)", line)
    return tokens


def __is_valid(instruction_tokens):
    is_valid_instruction = False
    if len(instruction_tokens) == 4:
        operation = instruction_tokens[0]
        field1 = instruction_tokens[1]
        field2 = instruction_tokens[2]
        field3 = instruction_tokens[3]
        if __operation_is_valid(operation):
            has_valid_fields = False
            if __operation_is_add_sub(operation) or __operation_is_mul_div(operation):
                has_valid_fields = __is_valid_f_reg(field1) and __is_valid_f_reg(field2) and __is_valid_f_reg(field3)
            elif __operation_is_load(operation) or __operation_is_store(operation):
                has_valid_fields = __is_valid_f_reg(field1) and __is_valid_num(field2) and __is_valid_x_reg(field3)
            is_valid_instruction = has_valid_fields
    return is_valid_instruction


def __operation_is_load(operation):
    return operation in ['flw']


def __operation_is_store(operation):
    return operation in ['fsw']


def __operation_is_add_sub(operation):
    return operation in ['fadd', 'fsub']


def __operation_is_mul_div(operation):
    return operation in ['fmul', 'fdiv']


def __operation_is_valid(operation):
    return \
        __operation_is_add_sub(operation) or __operation_is_mul_div(operation) or \
        __operation_is_load(operation) or __operation_is_store(operation)


def __is_valid_f_reg(field):
    f_reg_pattern = r"(^(f[0-9]||f1[0-9]||f2[0-9]|f3[0-1])$)"
    return re.search(f_reg_pattern, field) is not None


def __is_valid_x_reg(field):
    x_reg_pattern = r"(^(x[0-9]||x1[0-9]||x2[0-9]|x3[0-1])$)"
    return re.search(x_reg_pattern, field) is not None


def __is_valid_num(field):
    x_num_pattern = R"(^-?\d+$)"
    return re.search(x_num_pattern, field) is not None


def __make_instruction_from(line, instruction_tokens):
    operation = instruction_tokens[0]
    field1 = instruction_tokens[1]
    field2 = instruction_tokens[2]
    field3 = instruction_tokens[3]
    inst = Instruction(line)
    inst.operation = operation
    if __operation_is_add_sub(operation) or __operation_is_mul_div(operation):
        inst.destination = field1
        inst.source1 = field2
        inst.source2 = field3
    elif __operation_is_load(operation):
        inst.destination = field1
        inst.offset = field2
        inst.source1 = field3
    elif __operation_is_store(operation):
        inst.source1 = field1
        inst.offset = field2
        inst.source2 = field3
    return inst
