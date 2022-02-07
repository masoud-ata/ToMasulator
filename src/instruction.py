class Instruction:
    LOAD = 'flw'
    STORE = 'fsw'
    ADD = 'fadd'
    SUB = 'fsub'
    MUL = 'fmul'
    DIV = 'fdiv'

    def __init__(self, string):
        self.raw_text = string
        self.operation = ""
        self.destination = ""
        self.source1 = ""
        self.source2 = ""
        self.offset = ""

    def is_load(self):
        return self.operation == Instruction.LOAD

    def is_store(self):
        return self.operation == Instruction.STORE

    def is_add(self):
        return self.operation == Instruction.ADD

    def is_sub(self):
        return self.operation == Instruction.SUB

    def is_mul(self):
        return self.operation == Instruction.MUL

    def is_div(self):
        return self.operation == Instruction.DIV

    def is_load_store(self):
        return self.is_load() or self.is_store()

    def is_add_sub(self):
        return self.is_add() or self.is_sub()

    def is_mul_div(self):
        return self.is_mul() or self.is_div()
