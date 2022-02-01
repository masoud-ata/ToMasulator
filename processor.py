from enum import Enum
from typing import List

from instruction import Instruction

INSTRUCTION_QUEUE_SLOT_NUMS = 3
ADD_SUB_RS_NUMS = 3
MUL_DIV_RS_NUMS = 2
LOAD_STORE_RS_NUMS = 4

ADD_SUB_LATENCY_CYCLES = 3
MUL_DIV_LATENCY_CYCLES = 7
LOAD_STORE_LATENCY_CYCLES = 1


class Processor:
    def __init__(self):
        self.locked_and_loaded = False
        self.instruction_memory = InstructionMemory()
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.data_memory = _DataMemory(self)
        self.common_data_bus = _CommonDataBus(self)
        self.instruction_queue = _InstructionQueue()
        self.add_sub_reservation_stations = []
        self.mul_div_reservation_stations = []
        self.load_store_reservation_stations = []
        for i in range(ADD_SUB_RS_NUMS):
            self.add_sub_reservation_stations.append(_ReservationStation(cpu=self, latency_in_cycles=ADD_SUB_LATENCY_CYCLES))
        for i in range(MUL_DIV_RS_NUMS):
            self.mul_div_reservation_stations.append(_ReservationStation(cpu=self, latency_in_cycles=MUL_DIV_LATENCY_CYCLES))
        for i in range(LOAD_STORE_RS_NUMS):
            self.load_store_reservation_stations.append(_ReservationStation(cpu=self, latency_in_cycles=LOAD_STORE_LATENCY_CYCLES))
        self.scheduler = _Scheduler(self)

    def reset(self):
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.instruction_queue.reset()
        self.data_memory.reset()
        self.common_data_bus.reset()
        all_rs = self.add_sub_reservation_stations + self.mul_div_reservation_stations + self.load_store_reservation_stations
        for rs in all_rs:
            rs.reset()
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
            self.scheduler.arbitrate()

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
        ATTEMPT_MEMORY_ACCESS = 5
        ATTEMPT_WRITE = 6
        WRITE_BACK = 7

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
        self.memory_access_succeeded = False

    def reset(self):
        self.state = self.State.FREE
        self.source1_provider = -1
        self.source2_provider = -1
        self.instruction = None
        self.counter = 0
        self.issue_number = 0
        self.write_succeeded = False
        self.memory_access_succeeded = False

    def tick(self):
        if self.state == self.State.ISSUED:
            if self.source1_provider == -1 and self.source2_provider == -1:
                self.state = self.State.EXECUTING
            else:
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
                else:
                    self.state = self.State.WAITING
        elif self.state == self.State.WAITING:
            # FIXME: Repetetive code as above
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
                if self.instruction.operation == "fsw" or self.instruction.operation == "flw":
                    self.cpu.data_memory.attempt_access(self)
                    self.state = self.State.ATTEMPT_MEMORY_ACCESS
                else:
                    self.cpu.common_data_bus.attempt_write(self)
                    self.state = self.State.ATTEMPT_WRITE
        elif self.state == self.State.ATTEMPT_MEMORY_ACCESS:
            if self.memory_access_succeeded:
                self.state = self.State.MEMORY
        elif self.state == self.State.MEMORY:
            if self.instruction.operation == "fsw":
                self.reset()
            else:
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
        self.pending_writes: List[_ReservationStation] = []
        self.writing_rs_id = 0
        self.writing_rs = None

    def reset(self):
        self.pending_writes: List[_ReservationStation] = []
        self.writing_rs_id = 0

    def attempt_write(self, rs: _ReservationStation):
        self.pending_writes.append(rs)

    def arbitrate_writes(self):
        self.writing_rs_id = 0
        self.writing_rs = None
        if len(self.pending_writes) > 0:
            sorted_pending_writes = sorted(self.pending_writes, key=lambda x: x.issue_number)
            writing_rs = sorted_pending_writes[0]
            self.writing_rs_id = id(writing_rs)
            self.writing_rs = writing_rs
            writing_rs.write_succeeded = True
            writing_rs.state = writing_rs.State.WRITE_BACK
            self.pending_writes.remove(writing_rs)


class _DataMemory:
    def __init__(self, cpu: Processor):
        self.cpu = cpu
        self.pending_accesses: List[_ReservationStation] = []
        self.requesting_rs_id = 0

    def reset(self):
        self.pending_accesses: List[_ReservationStation] = []
        self.requesting_rs_id = 0

    def attempt_access(self, rs: _ReservationStation):
        self.pending_accesses.append(rs)

    def arbitrate_accesses(self):
        self.requesting_rs_id = 0
        if len(self.pending_accesses) > 0:
            sorted_pending_accesses = sorted(self.pending_accesses, key=lambda x: x.issue_number)
            requesting_rs = sorted_pending_accesses[0]
            self.requesting_rs_id = id(requesting_rs)
            requesting_rs.write_succeeded = True
            requesting_rs.state = requesting_rs.State.MEMORY
            self.pending_accesses.remove(requesting_rs)


class _Scheduler:
    REGISTER_FILE = -1

    def __init__(self, cpu: Processor):
        self.cpu = cpu
        self.issue_number = 0
        self.register_stat = {"": _Scheduler.REGISTER_FILE}
        for i in range(32):
            self.register_stat["f" + str(i)] = _Scheduler.REGISTER_FILE

    def reset(self):
        self.issue_number = 0
        self.register_stat = {"": _Scheduler.REGISTER_FILE}
        for i in range(32):
            self.register_stat["f" + str(i)] = _Scheduler.REGISTER_FILE

    def handle(self, instruction: Instruction):
        issued = False
        if instruction.operation == "fadd" or instruction.operation == "fsub":
            for rs in self.cpu.add_sub_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_math_inst_to_reservation_station(rs, instruction)
                    issued = True
                    break
        elif instruction.operation == "fmul" or instruction.operation == "fdiv":
            for rs in self.cpu.mul_div_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_math_inst_to_reservation_station(rs, instruction)
                    issued = True
                    break
        elif instruction.operation == "flw":
            for rs in self.cpu.load_store_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_load_inst_to_reservation_station(rs, instruction)
                    issued = True
                    break
        elif instruction.operation == "fsw":
            for rs in self.cpu.load_store_reservation_stations:
                if rs.state == rs.State.FREE:
                    self.__assign_store_inst_to_reservation_station(rs, instruction)
                    issued = True
                    break
        return issued

    def __assign_math_inst_to_reservation_station(self, rs, instruction):
        rs.instruction = instruction
        rs.state = rs.State.ISSUED
        rs.source1_provider = self.register_stat[instruction.source1]
        rs.source2_provider = self.register_stat[instruction.source2]
        self.register_stat[instruction.destination] = id(rs)
        rs.issue_number = self.issue_number
        self.issue_number += 1

    def __assign_load_inst_to_reservation_station(self, rs, instruction):
        rs.instruction = instruction
        rs.state = rs.State.ISSUED
        rs.source1_provider = _Scheduler.REGISTER_FILE
        rs.source2_provider = _Scheduler.REGISTER_FILE
        self.register_stat[instruction.destination] = id(rs)
        rs.issue_number = self.issue_number
        self.issue_number += 1

    def __assign_store_inst_to_reservation_station(self, rs, instruction):
        rs.instruction = instruction
        rs.state = rs.State.ISSUED
        rs.source1_provider = self.register_stat[instruction.source1]
        rs.source2_provider = _Scheduler.REGISTER_FILE
        rs.issue_number = self.issue_number
        self.issue_number += 1

    def update_register_stat(self):
        writing_rs = self.cpu.common_data_bus.writing_rs
        if writing_rs is not None:
            this_rs_is_the_provider = self.cpu.scheduler.register_stat[writing_rs.instruction.destination] == id(writing_rs)
            if this_rs_is_the_provider:
                self.cpu.scheduler.register_stat[writing_rs.instruction.destination] = _Scheduler.REGISTER_FILE

    def tick(self):
        for rs in self.cpu.add_sub_reservation_stations:
            rs.tick()
        for rs in self.cpu.mul_div_reservation_stations:
            rs.tick()
        for rs in self.cpu.load_store_reservation_stations:
            rs.tick()

    def arbitrate(self):
        self.cpu.common_data_bus.arbitrate_writes()
        self.update_register_stat()
        self.cpu.data_memory.arbitrate_accesses()
