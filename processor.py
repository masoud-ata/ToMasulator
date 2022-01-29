from instruction import Instruction

INSTRUCTION_QUEUE_SLOT_NUMS = 3
ADD_SUB_RS_NUMS = 3
MUL_DIV_RS_NUMS = 4


class Processor:
    def __init__(self):
        self.locked_and_loaded = False
        self.instruction_memory = InstructionMemory()
        self.instruction_pointer = 0
        self.instruction_queue = _InstructionQueue()
        self.add_sub_reservation_stations = []
        self.mul_div_reservation_stations = []
        for i in range(ADD_SUB_RS_NUMS):
            self.add_sub_reservation_stations.append(_ReservationStation(3))
        for i in range(MUL_DIV_RS_NUMS):
            self.mul_div_reservation_stations.append(_ReservationStation(5))
        self.scheduler = _Scheduler(self)

    def reset(self):
        self.instruction_pointer = 0
        self.instruction_queue = _InstructionQueue()
        for i in range(ADD_SUB_RS_NUMS):
            self.add_sub_reservation_stations[i].reset()
        for i in range(MUL_DIV_RS_NUMS):
            self.mul_div_reservation_stations[i].reset()

    def upload_to_memory(self, instructions):
        self.locked_and_loaded = True
        self.instruction_memory.upload(instructions)
        self.__fill_instruction_queue()

    def tick(self):
        if self.locked_and_loaded:
            instruction = self.instruction_queue.top()
            issued = self.scheduler.handle(instruction)
            if issued:
                self.issue_instruction()
            self.scheduler.tick()

    def issue_instruction(self):
        self.instruction_queue.consume()
        if not self.__is_program_finished():
            new_instruction = self.__fetch_instruction()
            self.instruction_queue.insert(new_instruction)

    def __fill_instruction_queue(self):
        for i in range(self.instruction_queue.num_empty_slots()):
            instruction = self.__fetch_instruction()
            if instruction is not None:
                self.instruction_queue.insert(instruction)
            else:
                break

    def __fetch_instruction(self):
        instruction = self.instruction_memory[self.instruction_pointer]
        self.instruction_pointer += 1
        return instruction

    def __is_program_finished(self):
        return self.instruction_pointer == len(self.instruction_memory.instructions)


class InstructionMemory:
    def __init__(self):
        self.instructions = []
        self.num_instructions = 0

    def upload(self, instructions):
        self.instructions = instructions
        self.num_instructions = len(instructions)

    def __getitem__(self, index):
        if isinstance(index, int) and index < self.num_instructions:
            return self.instructions[index]
        return None


class _ReservationStation:
    def __init__(self, latency_in_cycles):
        self.busy = False
        self.instruction = None
        self.counter = 0
        self.latency_in_cycles = latency_in_cycles

    def reset(self):
        self.busy = False
        self.instruction = None
        self.counter = 0

    def tick(self):
        if self.busy:
            self.counter += 1
            if self.counter == self.latency_in_cycles:
                self.reset()


class _InstructionQueue:
    def __init__(self):
        self.instructions = []

    def has_pending_instructions(self):
        return len(self.instructions) > 0

    def has_space(self):
        return len(self.instructions) < INSTRUCTION_QUEUE_SLOT_NUMS

    def num_empty_slots(self):
        return INSTRUCTION_QUEUE_SLOT_NUMS - len(self.instructions)

    def insert(self, instruction):
        if self.has_space():
            self.instructions.append(instruction)

    def consume(self):
        if len(self.instructions) != 0:
            return self.instructions.pop(0)
        return None

    def top(self):
        if len(self.instructions) != 0:
            return self.instructions[0]
        else:
            return None

    def __getitem__(self, index):
        if isinstance(index, int) and index < INSTRUCTION_QUEUE_SLOT_NUMS:
            return self.instructions[index]
        return None


class _Scheduler:
    def __init__(self, cpu: Processor):
        self.cpu = cpu

    def handle(self, instruction: Instruction):
        issued = False
        if instruction.operation == "fadd" or instruction.operation == "fsub":
            for rs in self.cpu.add_sub_reservation_stations:
                if not rs.busy:
                    rs.instruction = instruction
                    rs.busy = True
                    issued = True
                    break
        elif instruction.operation == "fmul" or instruction.operation == "fdiv":
            for rs in self.cpu.mul_div_reservation_stations:
                if not rs.busy:
                    rs.instruction = instruction
                    rs.busy = True
                    issued = True
                    break
        elif instruction.operation == "flw" or instruction.operation == "fsw":
            issued = True
        return issued

    def tick(self):
        for rs in self.cpu.add_sub_reservation_stations:
            rs.tick()
        for rs in self.cpu.mul_div_reservation_stations:
            rs.tick()
