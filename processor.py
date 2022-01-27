from instruction import Instruction

QUEUE_SIZE = 3


class Processor:
    def __init__(self):
        self.instruction_pointer = 0
        self.instruction_memory = InstructionMemory()
        self.instruction_issue_queue = []

    def reset(self):
        self.instruction_pointer = 0
        self.instruction_issue_queue = []

    def load(self, instructions):
        self.instruction_memory.load(instructions)
        self.__fill_issue_queue()

    def __fill_issue_queue(self):
        for slot_number in range(QUEUE_SIZE):
            instruction = self.__fetch_instruction()
            if instruction is not None:
                self.instruction_issue_queue.append(instruction)

    def __fetch_instruction(self):
        instruction = self.instruction_memory[self.instruction_pointer]
        self.instruction_pointer += 1
        return instruction


class InstructionMemory:
    def __init__(self):
        self.instructions = []
        self.num_instructions = 0

    def load(self, instructions):
        self.instructions = instructions
        self.num_instructions = len(instructions)

    def __getitem__(self, index):
        if isinstance(index, int) and index < self.num_instructions:
            return self.instructions[index]
        return None
