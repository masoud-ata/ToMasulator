class Instruction:
    def __init__(self, string):
        self.raw_text = string
        self.operation = ""
        self.destination = ""
        self.source1 = ""
        self.source2 = ""
        self.offset = ""
