from typing import List

from processor_components import InstructionMemory, ReservationStation, InstructionQueue, CommonDataBus, DataMemory, Scheduler

ADD_SUB_LATENCY_CYCLES = 3
MUL_DIV_LATENCY_CYCLES = 7
LOAD_STORE_LATENCY_CYCLES = 1

ADD_SUB_RS_NUMS = 3
MUL_DIV_RS_NUMS = 2
LOAD_STORE_RS_NUMS = 4


class Processor:
    def __init__(self):
        self.num_cycles_load_store = LOAD_STORE_LATENCY_CYCLES
        self.num_cycles_add_sub = ADD_SUB_LATENCY_CYCLES
        self.num_cycles_mul_div = MUL_DIV_LATENCY_CYCLES
        self.num_rerevations_station_load_store = LOAD_STORE_RS_NUMS
        self.num_rerevation_stations_add_sub = ADD_SUB_RS_NUMS
        self.get_num_rerevation_stations_mul_div = MUL_DIV_RS_NUMS

        self.program_loaded = False
        self.instruction_memory = InstructionMemory()
        self.instruction_pointer = 0
        self.cycle_count = 0
        self.data_memory = DataMemory(self)
        self.common_data_bus = CommonDataBus(self)
        self.instruction_queue = InstructionQueue()
        self.add_sub_reservation_stations: List[ReservationStation] = []
        self.mul_div_reservation_stations: List[ReservationStation] = []
        self.load_store_reservation_stations: List[ReservationStation] = []
        self.set_reservation_station_sizes(self.num_rerevation_stations_add_sub, self.get_num_rerevation_stations_mul_div, self.num_rerevations_station_load_store)
        self.scheduler = Scheduler(self)

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

    def set_latency_cycles(self, num_cycles_load_store, num_cycles_add_sub, num_cycles_mul_div):
        self.num_cycles_load_store = num_cycles_load_store
        self.num_cycles_add_sub = num_cycles_add_sub
        self.num_cycles_mul_div = num_cycles_mul_div
        for rs in self.load_store_reservation_stations:
            rs.latency_in_cycles = num_cycles_load_store
        for rs in self.add_sub_reservation_stations:
            rs.latency_in_cycles = num_cycles_add_sub
        for rs in self.mul_div_reservation_stations:
            rs.latency_in_cycles = num_cycles_mul_div

    def set_reservation_station_sizes(self, load_store_rs_nums, add_sub_rs_nums, mul_div_rs_nums):
        self.num_rerevations_station_load_store = load_store_rs_nums
        self.num_rerevation_stations_add_sub = add_sub_rs_nums
        self.get_num_rerevation_stations_mul_div = mul_div_rs_nums
        self.load_store_reservation_stations.clear()
        self.add_sub_reservation_stations.clear()
        self.mul_div_reservation_stations.clear()
        for i in range(load_store_rs_nums):
            self.load_store_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_load_store))
        for i in range(add_sub_rs_nums):
            self.add_sub_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_add_sub))
        for i in range(mul_div_rs_nums):
            self.mul_div_reservation_stations.append(ReservationStation(cpu=self, latency_in_cycles=self.num_cycles_mul_div))

    def upload_to_memory(self, instructions):
        self.program_loaded = True
        self.instruction_memory.upload(instructions)
        self.__fill_instruction_queue()

    def tick(self):
        if self.program_loaded:
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

    def get_instruction_texts_in_queue(self) -> List[str]:
        instructions: List[str] = []
        for inst in self.instruction_queue.instructions:
            instructions.append(inst.raw_text)
        return instructions

    # def get_instruction_texts_in_add_sub_reservation_stations(self) -> List[str]:
    #     instructions: List[str] = []
    #     for rs in self.add_sub_reservation_stations:
    #         instructions.append(rs.instruction.raw_text)
    #     return instructions

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

    def get_reservation_stations_info(self):
        rs_states = []
        all_rs = self.add_sub_reservation_stations + self.mul_div_reservation_stations + self.load_store_reservation_stations
        for rs in all_rs:
            rs_states.append((str(rs.state.name), id(rs.instruction)))
        return rs_states