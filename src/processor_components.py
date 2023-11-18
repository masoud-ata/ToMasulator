from enum import auto
from typing import List

from instruction import Instruction

INSTRUCTION_QUEUE_SLOT_NUMS = 3

REGISTER_FILE = -1
COMMON_DATA_BUS = REGISTER_FILE
REGISTER_FILE_OR_COMMON_DATA_BUS = REGISTER_FILE


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


class ReservationStation:
    class State:
        FREE = auto(), ""
        JUST_ISSUED = auto(), "I"
        WAITING_FOR_OPERANDS = auto(), "-"
        EXECUTING = auto(), "E"
        MEMORY = auto(), "M"
        ATTEMPT_MEMORY_ACCESS = auto(), "-"
        ATTEMPT_WRITEBACK = auto(), "-"
        WRITE_BACK = auto(), "W"
        READ_OPERANDS = auto(), "R"

    def __init__(self, cpu, latency_in_cycles):
        self._cpu = cpu
        self._latency_in_cycles = latency_in_cycles
        self.state = self.State.FREE
        self.source1_provider = REGISTER_FILE
        self.source2_provider = REGISTER_FILE
        self.instruction = None
        self._execution_counter = 0
        self.issue_number = 0
        self._writeback_succeeded = False
        self._memory_access_succeeded = False

    def reset(self) -> None:
        self.state = self.State.FREE
        self.source1_provider = REGISTER_FILE
        self.source2_provider = REGISTER_FILE
        self.instruction = None
        self._execution_counter = 0
        self.issue_number = 0
        self._writeback_succeeded = False
        self._memory_access_succeeded = False

    def id(self) -> int:
        return id(self)

    def is_free(self) -> bool:
        return self.state is self.State.FREE

    def is_busy(self) -> bool:
        return not self.is_free()

    def get_state_abbreviation(self) -> str:
        _, state_abbreviation = self.state
        if self.state is self.State.EXECUTING:
            state_abbreviation += str(self._execution_counter + 1)
        return state_abbreviation

    def issue(self, instruction, issue_number) -> None:
        self.instruction = instruction
        self.state = self.State.JUST_ISSUED
        self.issue_number = issue_number

    def set_memory_access_success(self, status) -> None:
        self._memory_access_succeeded = status

    def set_writeback_success(self, status) -> None:
        self._writeback_succeeded = status

    def tick(self) -> None:
        if self.state is self.State.JUST_ISSUED:
            self._state_just_issued_logic()
        elif self.state is self.State.WAITING_FOR_OPERANDS:
            self._state_waiting_for_operands_logic()
        elif self.state is self.State.READ_OPERANDS:
            self.state = self.State.EXECUTING
        elif self.state is self.State.EXECUTING:
            self._state_executing_logic()
        elif self.state is self.State.ATTEMPT_MEMORY_ACCESS:
            pass  # Resolved in after_tick()
        elif self.state is self.State.MEMORY:
            self._state_memory_logic()
        elif self.state is self.State.ATTEMPT_WRITEBACK:
            pass  # Resolved in after_tick()
        elif self.state is self.State.WRITE_BACK:
            self.reset()

    def after_tick(self) -> None:
        if self.state is self.State.ATTEMPT_MEMORY_ACCESS and self._memory_access_succeeded:
            self.state = self.State.MEMORY
            self._memory_access_succeeded = False
        if self.state is self.State.ATTEMPT_WRITEBACK and self._writeback_succeeded:
            self.state = self.State.WRITE_BACK
            self._writeback_succeeded = False

    def is_issued_earlier_than(self, rs: 'ReservationStation') -> bool:
        return self.issue_number < rs.issue_number

    def has_write_after_read_hazard_with(self, rs: 'ReservationStation') -> bool:
        i_am_issued_earlier = self.is_issued_earlier_than(rs)
        i_still_need_operands = self.state == self.State.WAITING_FOR_OPERANDS or self.state == self.State.READ_OPERANDS
        there_is_war_hazard = i_am_issued_earlier and i_still_need_operands and self.has_same_source_as_destination_of(rs)
        return there_is_war_hazard

    def has_same_source_as_destination_of(self, rs: 'ReservationStation') -> bool:
        return self.instruction.source1 == rs.instruction.destination or self.instruction.source2 == rs.instruction.destination

    def _state_just_issued_logic(self) -> None:
        tomasulo = self._cpu.scheduler.algorithm_is_tomasulo()
        inst_is_store = self.instruction.is_store()
        if self._operands_are_ready():
            self.state = self.State.EXECUTING if tomasulo else self.State.READ_OPERANDS
        else:
            self.state = self.State.EXECUTING if tomasulo and inst_is_store else self.State.WAITING_FOR_OPERANDS

    def _state_waiting_for_operands_logic(self) -> None:
        tomasulo = self._cpu.scheduler.algorithm_is_tomasulo()
        if self._operands_are_ready():
            if self.instruction.is_store():
                if tomasulo:
                    self._cpu.data_memory.attempt_access(self)
                    self.state = self.State.ATTEMPT_MEMORY_ACCESS
                else:
                    self.state = self.State.READ_OPERANDS
            else:
                self.state = self.State.EXECUTING if tomasulo else self.State.READ_OPERANDS

    def _state_executing_logic(self) -> None:
        self._execution_counter += 1
        if self._execution_counter == self._latency_in_cycles:
            if self.instruction.is_load() or (self.instruction.is_store() and self._operands_are_ready()):
                self._cpu.data_memory.attempt_access(self)
                self.state = self.State.ATTEMPT_MEMORY_ACCESS
            elif self.instruction.is_store() and not self._operands_are_ready():
                self.state = self.State.WAITING_FOR_OPERANDS
            else:
                self._cpu.common_data_bus.attempt_write(self)
                self.state = self.State.ATTEMPT_WRITEBACK

    def _state_memory_logic(self) -> None:
        if self.instruction.is_store():
            self.reset()
        else:
            self._cpu.common_data_bus.attempt_write(self)
            self.state = self.State.ATTEMPT_WRITEBACK

    def _operands_are_ready(self) -> bool:
        op1_ready = self.source1_provider == REGISTER_FILE_OR_COMMON_DATA_BUS
        op2_ready = self.source2_provider == REGISTER_FILE_OR_COMMON_DATA_BUS
        if not op1_ready and self.source1_provider == self._cpu.common_data_bus.writing_rs_id():
            self.source1_provider = COMMON_DATA_BUS
            op1_ready = True
        if not op2_ready and self.source2_provider == self._cpu.common_data_bus.writing_rs_id():
            self.source2_provider = COMMON_DATA_BUS
            op2_ready = True
        return op1_ready and op2_ready


class InstructionQueue:
    def __init__(self):
        self.instructions: List[Instruction] = []

    def reset(self):
        self.instructions.clear()

    def has_pending_instructions(self):
        return len(self.instructions) > 0

    @staticmethod
    def get_num_slots():
        return INSTRUCTION_QUEUE_SLOT_NUMS

    def get_instructions_list_text(self) -> List[str]:
        inst_list = []
        for inst in self.instructions:
            inst_list.append(inst.raw_text)
        return inst_list

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


class CommonDataBus:
    def __init__(self, cpu):
        self._cpu = cpu
        self._pending_rs_writers: List[ReservationStation] = []
        self._writing_rs_id = 0
        self._writing_rs = None

    def reset(self) -> None:
        self._pending_rs_writers.clear()
        self._writing_rs_id = 0
        self._writing_rs = None

    def attempt_write(self, rs: ReservationStation) -> None:
        self._pending_rs_writers.append(rs)

    def arbitrate_write_backs(self) -> None:
        self._writing_rs_id = 0
        self._writing_rs = None
        if self._we_have_pending_writes():
            sorted_writers = sorted(self._pending_rs_writers, key=lambda x: x.issue_number)
            self._handle_potential_writeback(sorted_writers)

    def get_writing_rs(self) -> ReservationStation:
        return self._writing_rs

    def writing_rs_id(self) -> int:
        return self._writing_rs_id

    def _we_have_pending_writes(self) -> bool:
        return len(self._pending_rs_writers) > 0

    def _handle_potential_writeback(self, sorted_writers) -> None:
        if self._cpu.scheduler.algorithm_is_tomasulo():
            writing_rs = sorted_writers[0]
            self._perform_write_back(writing_rs)
        else:
            for writing_rs in sorted_writers:
                found_war = self._check_for_write_after_read_hazards(writing_rs)
                if not found_war:
                    self._perform_write_back(writing_rs)
                    break

    def _perform_write_back(self, writing_rs) -> None:
        self._writing_rs_id = writing_rs.id()
        self._writing_rs = writing_rs
        writing_rs.set_writeback_success(True)
        self._pending_rs_writers.remove(writing_rs)

    def _check_for_write_after_read_hazards(self, writing_rs) -> bool:
        found_war = False
        for rs in self._cpu.get_all_reservation_stations():
            found_war = rs.is_busy() and rs.has_write_after_read_hazard_with(writing_rs)
            if found_war:
                break
        return found_war


class DataMemory:
    def __init__(self):
        self._pending_accesses: List[ReservationStation] = []

    def reset(self) -> None:
        self._pending_accesses.clear()

    def _there_are_pending_accesses(self) -> bool:
        return len(self._pending_accesses) > 0

    def attempt_access(self, rs: ReservationStation) -> None:
        self._pending_accesses.append(rs)

    def arbitrate_accesses(self) -> None:
        if self._there_are_pending_accesses():
            sorted_pending_accesses = sorted(self._pending_accesses, key=lambda x: x.issue_number)
            winning_rs = sorted_pending_accesses[0]
            winning_rs.set_memory_access_success(True)
            self._pending_accesses.remove(winning_rs)


class Scheduler:
    def __init__(self, cpu):
        self._cpu = cpu
        self._algorithm_is_tomasulo = True
        self._issue_number = 0
        self._register_stat = {"": REGISTER_FILE}
        for i in range(32):
            self._register_stat["f" + str(i)] = REGISTER_FILE

    def reset(self) -> None:
        self._issue_number = 0
        self._register_stat = {f'f{i}': REGISTER_FILE for i in range(32)}
        self._register_stat[""] = REGISTER_FILE

    def set_algorithm(self, is_tomasulo=True) -> None:
        self._algorithm_is_tomasulo = is_tomasulo

    def algorithm_is_tomasulo(self) -> bool:
        return self._algorithm_is_tomasulo

    def algorithm_is_scoreboard(self) -> bool:
        return not self._algorithm_is_tomasulo

    def tick(self) -> None:
        for rs in self._cpu.get_all_reservation_stations():
            rs.tick()
        issued = self.attempt_issue(self._cpu.instruction_queue.top())
        if issued:
            self._cpu.update_instruction_queue()
        self.arbitrate()
        for rs in self._cpu.get_all_reservation_stations():
            rs.after_tick()

    def attempt_issue(self, instruction: Instruction) -> bool:
        issued = False
        if instruction is None or (self.algorithm_is_scoreboard() and self._there_is_write_after_write_hazard(instruction)):
            pass
        elif instruction.is_add_sub():
            issued = self._attempt_assign_add_sub_inst(instruction)
        elif instruction.is_mul_div():
            issued = self._attempt_assign_mul_div_inst(instruction)
        elif instruction.is_load():
            issued = self._attempt_assign_load_inst(instruction)
        elif instruction.is_store():
            issued = self._attempt_assign_store_inst(instruction)
        return issued

    def arbitrate(self) -> None:
        self._cpu.common_data_bus.arbitrate_write_backs()
        self.update_register_stat()
        self._cpu.data_memory.arbitrate_accesses()

    def update_register_stat(self) -> None:
        writing_rs = self._cpu.common_data_bus.get_writing_rs()
        if writing_rs is not None:
            this_rs_is_the_provider = self._register_stat[writing_rs.instruction.destination] == writing_rs.id()
            if this_rs_is_the_provider:
                self._register_stat[writing_rs.instruction.destination] = REGISTER_FILE

    def _attempt_assign_add_sub_inst(self, instruction) -> bool:
        assigned = False
        for rs in self._cpu.add_sub_reservation_stations:
            if rs.is_free():
                self._assign_math_inst_to_reservation_station(rs, instruction)
                assigned = True
                break
        return assigned

    def _attempt_assign_mul_div_inst(self, instruction) -> bool:
        assigned = False
        for rs in self._cpu.mul_div_reservation_stations:
            if rs.is_free():
                self._assign_math_inst_to_reservation_station(rs, instruction)
                assigned = True
                break
        return assigned

    def _attempt_assign_load_inst(self, instruction) -> bool:
        assigned = False
        for rs in self._cpu.load_store_reservation_stations:
            if rs.is_free():
                self._assign_load_inst_to_reservation_station(rs, instruction)
                assigned = True
                break
        return assigned

    def _attempt_assign_store_inst(self, instruction) -> bool:
        assigned = False
        for rs in self._cpu.load_store_reservation_stations:
            if rs.is_free():
                self._assign_store_inst_to_reservation_station(rs, instruction)
                assigned = True
                break
        return assigned

    def _assign_math_inst_to_reservation_station(self, rs, instruction) -> None:
        rs.source1_provider = self._register_stat[instruction.source1]
        rs.source2_provider = self._register_stat[instruction.source2]
        self._register_stat[instruction.destination] = rs.id()
        self._complete_assignment(rs, instruction)

    def _assign_load_inst_to_reservation_station(self, rs, instruction) -> None:
        rs.source1_provider = REGISTER_FILE
        rs.source2_provider = REGISTER_FILE
        self._register_stat[instruction.destination] = rs.id()
        self._complete_assignment(rs, instruction)

    def _assign_store_inst_to_reservation_station(self, rs, instruction) -> None:
        rs.source1_provider = self._register_stat[instruction.source1]
        rs.source2_provider = REGISTER_FILE
        self._complete_assignment(rs, instruction)

    def _complete_assignment(self, rs, instruction) -> None:
        rs.issue(instruction, self._issue_number)
        self._issue_number += 1

    def _there_is_write_after_write_hazard(self, instruction) -> bool:
        return self._register_stat[instruction.destination] != REGISTER_FILE
