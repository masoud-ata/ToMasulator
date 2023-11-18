from typing import List

from window import MainWindow
from processor import Processor


class Controller:
    def __init__(self):
        self._cpu = Processor()
        self._ui = MainWindow(pos_x=300, pos_y=300, width=1610, height=600, title='ToMasulator', controller=self)
        self._ui.load_reset()

    def tick(self) -> None:
        self._cpu.tick()

    def reset(self) -> None:
        self._cpu.reset()

    def there_is_work_to_do(self) -> bool:
        return self._cpu.there_is_work_to_do()

    def upload_to_memory(self, instructions) -> None:
        self._cpu.upload_to_memory(instructions)

    def get_cycle_count(self) -> int:
        return self._cpu.cycle_count

    def get_num_instruction_queue_slots(self) -> int:
        return self._cpu.get_num_instruction_queue_slots()

    def get_num_cycles_load_store(self) -> int:
        return self._cpu.num_cycles_load_store

    def get_num_cycles_add_sub(self) -> int:
        return self._cpu.num_cycles_add_sub

    def get_num_cycles_mul_div(self) -> int:
        return self._cpu.num_cycles_mul_div

    def get_num_reservation_stations_load_store(self) -> int:
        return self._cpu.num_reservation_stations_load_store

    def get_num_reservation_stations_add_sub(self) -> int:
        return self._cpu.num_reservation_stations_add_sub

    def get_num_reservation_stations_mul_div(self) -> int:
        return self._cpu.num_reservation_stations_mul_div

    def set_num_cycles(self, num_cycles_load_store, num_cycles_add_sub, num_cycles_mul_div) -> None:
        self._cpu.set_latency_cycles(num_cycles_load_store, num_cycles_add_sub, num_cycles_mul_div)

    def get_instruction_texts_in_queue(self) -> List[str]:
        return self._cpu.get_instruction_texts_in_queue()

    def get_load_store_reservation_station_instruction_text(self, index) -> str:
        return self._cpu.get_load_store_reservation_station_instruction_text(index)

    def load_store_reservation_station_is_free(self, index) -> bool:
        return self._cpu.load_store_reservation_station_is_free(index)

    def load_store_reservation_station_is_just_issued(self, index) -> bool:
        return self._cpu.load_store_reservation_station_is_just_issued(index)

    def get_add_sub_reservation_station_instruction_text(self, index) -> str:
        return self._cpu.get_add_sub_reservation_station_instruction_text(index)

    def add_sub_reservation_station_is_free(self, index) -> bool:
        return self._cpu.add_sub_reservation_station_is_free(index)

    def add_sub_reservation_station_is_just_issued(self, index) -> bool:
        return self._cpu.add_sub_reservation_station_is_just_issued(index)

    def get_mul_div_reservation_station_instruction_text(self, index) -> str:
        return self._cpu.get_mul_div_reservation_station_instruction_text(index)

    def mul_div_reservation_station_is_free(self, index) -> bool:
        return self._cpu.mul_div_reservation_station_is_free(index)

    def mul_div_reservation_station_is_just_issued(self, index) -> bool:
        return self._cpu.mul_div_reservation_station_is_just_issued(index)

    def get_reservation_stations_instruction_states(self) -> List:
        return self._cpu.get_reservation_stations_instruction_states()

    def set_reservation_station_sizes(self, load_store_rs_nums, add_sub_rs_nums, mul_div_rs_nums) -> None:
        self._cpu.set_reservation_station_sizes(load_store_rs_nums, add_sub_rs_nums, mul_div_rs_nums)

    def set_scheduling_algorithm(self, algorithm) -> None:
        self._cpu.set_scheduling_algorithm(algorithm)
