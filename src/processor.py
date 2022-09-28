from typing import List

from processor_components import InstructionMemory, ReservationStation, InstructionQueue, CommonDataBus, DataMemory, Scheduler
from instruction import Instruction

LOAD_STORE_LATENCY_CYCLES = 1
ADD_SUB_LATENCY_CYCLES = 3
MUL_DIV_LATENCY_CYCLES = 7

LOAD_STORE_RS_NUMS = 4
ADD_SUB_RS_NUMS = 3
MUL_DIV_RS_NUMS = 2


class Processor:
    def __init__(self):
        self.num_cycles_load_store = LOAD_STORE_LATENCY_CYCLES
        self.num_cycles_add_sub = ADD_SUB_LATENCY_CYCLES
        self.num_cycles_mul_div = MUL_DIV_LATENCY_CYCLES
        self.num_reservation_stations_load_store = LOAD_STORE_RS_NUMS
        self.num_reservation_stations_add_sub = ADD_SUB_RS_NUMS
        self.num_reservation_stations_mul_div = MUL_DIV_RS_NUMS

        self.program_loaded = False
        self.instruction_memory = InstructionMemory()
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.data_memory = DataMemory()
        self.common_data_bus = CommonDataBus(self)
        self.instruction_queue = InstructionQueue()
        self.add_sub_reservation_stations: List[ReservationStation] = []
        self.mul_div_reservation_stations: List[ReservationStation] = []
        self.load_store_reservation_stations: List[ReservationStation] = []
        self.set_reservation_station_sizes(
            load_store_rs_nums=self.num_reservation_stations_load_store,
            add_sub_rs_nums=self.num_reservation_stations_add_sub,
            mul_div_rs_nums=self.num_reservation_stations_mul_div,
        )
        self.scheduler = Scheduler(self)

    def reset(self) -> None:
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.instruction_queue.reset()
        self.data_memory.reset()
        self.common_data_bus.reset()
        for rs in self.get_all_reservation_stations():
            rs.reset()
        self.scheduler.reset()

    def set_latency_cycles(self, num_cycles_load_store, num_cycles_add_sub, num_cycles_mul_div) -> None:
        self.num_cycles_load_store = num_cycles_load_store
        self.num_cycles_add_sub = num_cycles_add_sub
        self.num_cycles_mul_div = num_cycles_mul_div
        for rs in self.load_store_reservation_stations:
            rs._latency_in_cycles = num_cycles_load_store
        for rs in self.add_sub_reservation_stations:
            rs._latency_in_cycles = num_cycles_add_sub
        for rs in self.mul_div_reservation_stations:
            rs._latency_in_cycles = num_cycles_mul_div

    def set_reservation_station_sizes(self, load_store_rs_nums, add_sub_rs_nums, mul_div_rs_nums) -> None:
        self.num_reservation_stations_load_store = load_store_rs_nums
        self.num_reservation_stations_add_sub = add_sub_rs_nums
        self.num_reservation_stations_mul_div = mul_div_rs_nums
        self.load_store_reservation_stations.clear()
        self.add_sub_reservation_stations.clear()
        self.mul_div_reservation_stations.clear()
        for i in range(load_store_rs_nums):
            self.load_store_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_load_store))
        for i in range(add_sub_rs_nums):
            self.add_sub_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_add_sub))
        for i in range(mul_div_rs_nums):
            self.mul_div_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_mul_div))

    def upload_to_memory(self, instructions) -> None:
        self.program_loaded = True
        self.instruction_memory.upload(instructions)
        self._fill_instruction_queue()

    def tick(self) -> None:
        if self.program_loaded and self._there_is_work_to_do():
            self.cycle_count += 1
            self.scheduler.tick()

    def update_instruction_queue(self) -> None:
        self.instruction_queue.consume()
        if not self._is_program_finished():
            new_instruction = self._fetch_instruction()
            if new_instruction is not None:
                self.instruction_queue.insert(new_instruction)

    def get_all_reservation_stations(self) -> List[ReservationStation]:
        return self.load_store_reservation_stations + self.add_sub_reservation_stations + self.mul_div_reservation_stations

    def get_instruction_texts_in_queue(self) -> List[str]:
        return self.instruction_queue.get_instructions_list_text()

    def get_num_instruction_queue_slots(self) -> int:
        return self.instruction_queue.get_num_slots()

    def get_load_store_reservation_station_instruction_text(self, index) -> str:
        return self.load_store_reservation_stations[index].instruction.raw_text

    def load_store_reservation_station_is_free(self, index) -> bool:
        return self.load_store_reservation_stations[index].state == ReservationStation.State.FREE

    def load_store_reservation_station_is_just_issued(self, index) -> bool:
        return self.load_store_reservation_stations[index].state == ReservationStation.State.JUST_ISSUED

    def get_add_sub_reservation_station_instruction_text(self, index) -> str:
        return self.add_sub_reservation_stations[index].instruction.raw_text

    def add_sub_reservation_station_is_free(self, index) -> bool:
        return self.add_sub_reservation_stations[index].state == ReservationStation.State.FREE

    def add_sub_reservation_station_is_just_issued(self, index) -> bool:
        return self.add_sub_reservation_stations[index].state == ReservationStation.State.JUST_ISSUED

    def get_mul_div_reservation_station_instruction_text(self, index) -> str:
        return self.mul_div_reservation_stations[index].instruction.raw_text

    def mul_div_reservation_station_is_free(self, index) -> bool:
        return self.mul_div_reservation_stations[index].state == ReservationStation.State.FREE

    def mul_div_reservation_station_is_just_issued(self, index) -> bool:
        return self.mul_div_reservation_stations[index].state == ReservationStation.State.JUST_ISSUED

    def get_reservation_stations_instruction_states(self) -> List:
        instruction_state_table = []
        for rs in self.get_all_reservation_stations():
            if rs.state is not ReservationStation.State.FREE:
                instruction_id = id(rs.instruction)
                instruction_state_in_text = rs.get_state_abbreviation()
                instruction_state_table.append((instruction_id, instruction_state_in_text))
        return instruction_state_table

    def set_scheduling_algorithm(self, algorithm) -> None:
        self.scheduler.set_algorithm(is_tomasulo=algorithm == 'Tomasulo')

    def _there_is_work_to_do(self) -> bool:
        return not(self.cycle_count != 0 and self._all_reservation_stations_are_free())

    def _all_reservation_stations_are_free(self) -> bool:
        all_are_free = True
        for rs in self.get_all_reservation_stations():
            all_are_free = all_are_free and rs.is_free()
        return all_are_free

    def _fill_instruction_queue(self) -> None:
        for i in range(self.instruction_queue.num_empty_slots()):
            instruction = self._fetch_instruction()
            if instruction is not None:
                self.instruction_queue.insert(instruction)
            else:
                break

    def _fetch_instruction(self) -> Instruction:
        instruction = self.instruction_memory[self.instruction_pointer]
        self.instruction_pointer += 1
        return instruction

    def _is_program_finished(self):
        return self.instruction_pointer == len(self.instruction_memory.instructions)
