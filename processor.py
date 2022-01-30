from enum import Enum

from instruction import Instruction

INSTRUCTION_QUEUE_SLOT_NUMS = 3
ADD_SUB_RS_NUMS = 3
MUL_DIV_RS_NUMS = 4


class Processor:
    def __init__(self):
        self.locked_and_loaded = False
        self.instruction_memory = InstructionMemory()
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.common_data_bus = _CommonDataBus(self)
        self.instruction_queue = _InstructionQueue()
        self.add_sub_reservation_stations = []
        self.mul_div_reservation_stations = []
        for i in range(ADD_SUB_RS_NUMS):
            self.add_sub_reservation_stations.append(_ReservationStation(self, 3))
        for i in range(MUL_DIV_RS_NUMS):
            self.mul_div_reservation_stations.append(_ReservationStation(self, 5))
        self.scheduler = _Scheduler(self)

    def reset(self):
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.instruction_queue.reset()
        self.common_data_bus.reset()
        for i in range(ADD_SUB_RS_NUMS):
            self.add_sub_reservation_stations[i].reset()
        for i in range(MUL_DIV_RS_NUMS):
            self.mul_div_reservation_stations[i].reset()
        self.scheduler.reset()

    def upload_to_memory(self, instructions):
        self.locked_and_loaded = True
        self.instruction_memory.upload(instructions)
        self.__fill_instruction_queue()

    def tick(self):
        if self.locked_and_loaded:
            self.cycle_count += 1
            instruction = self.instruction_queue.top()
            self.scheduler.tick()
            if instruction is not None:
                issued = self.scheduler.handle(instruction)
                if issued:
                    self.issue_instruction()
            self.common_data_bus.arbitrate_writes()

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
    class State(Enum):
        FREE = 0
        ISSUED = 1
        WAITING = 2
        EXECUTING = 3
        MEMORY = 4
        ATTEMPT_WRITE = 5
        WRITE_BACK = 6

    def __init__(self, cpu: Processor, latency_in_cycles):
        self.cpu = cpu
        self.latency_in_cycles = latency_in_cycles
        self.state = self.State.FREE
        self.source1_provider = -1
        self.source2_provider = -1
        self.instruction = None
        self.counter = 0
        self.issue_number = 0
        self.write_succeeded = False

    def reset(self):
        self.state = self.State.FREE
        self.source1_provider = -1
        self.source2_provider = -1
        self.instruction = None
        self.counter = 0
        self.issue_number = 0
        self.write_succeeded = False

    def tick(self):
        if self.state == self.State.ISSUED:
            if self.source1_provider == -1 and self.source2_provider == -1:
                self.state = self.State.EXECUTING
            else:
                self.state = self.State.WAITING
        elif self.state == self.State.WAITING:
            op1_avilable = True
            op2_avilable = True
            if self.source1_provider != -1:
                op1_avilable = False
                if self.cpu.common_data_bus.writing_rs_id == self.source1_provider:
                    self.source1_provider = -1
                    op1_avilable = True
            if self.source2_provider != -1:
                op2_avilable = False
                if self.cpu.common_data_bus.writing_rs_id == self.source2_provider:
                    self.source2_provider = -1
                    op2_avilable = True
            if op1_avilable and op2_avilable:
                self.state = self.State.EXECUTING
        elif self.state == self.State.EXECUTING:
            self.counter += 1
            if self.counter == self.latency_in_cycles:
                self.cpu.common_data_bus.attempt_write(self)
                self.state = self.State.ATTEMPT_WRITE
        elif self.state == self.State.ATTEMPT_WRITE:
            if self.write_succeeded:
                self.state = self.State.WRITE_BACK
        elif self.state == self.State.WRITE_BACK:
            self.reset()


class _InstructionQueue:
    def __init__(self):
        self.instructions = []

    def reset(self):
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


class _CommonDataBus:
    def __init__(self, cpu: Processor):
        self.cpu = cpu
        self.pending_writes = []
        self.writing_rs_id = 0

    def reset(self):
        self.pending_writes = []
        self.writing_rs_id = 0

    def attempt_write(self, rs: _ReservationStation):
        self.pending_writes.append((id(rs), rs.issue_number, rs))

    def arbitrate_writes(self):
        self.writing_rs_id = 0
        if len(self.pending_writes) > 0:
            sorted_pending_writes = sorted(self.pending_writes, key=lambda tup: tup[1])
            self.writing_rs_id = sorted_pending_writes[0][0]
            sorted_pending_writes[0][2].write_succeeded = True
            sorted_pending_writes[0][2].state = sorted_pending_writes[0][2].State.WRITE_BACK
            self.pending_writes.remove(sorted_pending_writes[0])
            # FIXME
            if self.cpu.scheduler.register_stat[sorted_pending_writes[0][2].instruction.destination] == sorted_pending_writes[0][0]:
                self.cpu.scheduler.register_stat[sorted_pending_writes[0][2].instruction.destination] = -1


class _Scheduler:
    def __init__(self, cpu: Processor):
        self.cpu = cpu
        self.issue_number = 0
        self.register_stat = {"": -1}
        for i in range(32):
            self.register_stat["f"+str(i)] = -1

    def reset(self):
        self.issue_number = 0
        self.register_stat = {"": -1}
        for i in range(32):
            self.register_stat["f"+str(i)] = -1

    def handle(self, instruction: Instruction):
        issued = False
        if instruction.operation == "fadd" or instruction.operation == "fsub":
            for rs in self.cpu.add_sub_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_to_reservation_station(rs, instruction)
                    issued = True
                    break
        elif instruction.operation == "fmul" or instruction.operation == "fdiv":
            for rs in self.cpu.mul_div_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_to_reservation_station(rs, instruction)
                    issued = True
                    break
        elif instruction.operation == "flw" or instruction.operation == "fsw":
            issued = True
        return issued

    def __assign_to_reservation_station(self, rs, instruction):
        rs.instruction = instruction
        rs.state = rs.State.ISSUED
        rs.source1_provider = self.register_stat[instruction.source1]
        rs.source2_provider = self.register_stat[instruction.source2]
        self.register_stat[instruction.destination] = id(rs)
        rs.issue_number = self.issue_number
        self.issue_number += 1

    def tick(self):
        for rs in self.cpu.add_sub_reservation_stations:
            rs.tick()
        for rs in self.cpu.mul_div_reservation_stations:
            rs.tick()
