import sys
from PyQt5.QtWidgets import (QPushButton, QApplication, QLabel, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit)
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtCore import Qt

from gui import QCodeEditor

from processor import Processor
from assembler import assemble

DEFAULT_PROGRAM = \
    "fsw  f1, 0(x1) \nfadd f1, f2, f3 \nfsub f3, f4, f1\nfmul f5, f10, f10\n" \
    "fadd f8, f2, f3 \nfsub f9, f4, f6\nfmul f10, f10, f1\n"

ADD_SUB_LATENCY_CYCLES = 3
MUL_DIV_LATENCY_CYCLES = 7
LOAD_STORE_LATENCY_CYCLES = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.cpu = Processor(ADD_SUB_LATENCY_CYCLES, MUL_DIV_LATENCY_CYCLES, LOAD_STORE_LATENCY_CYCLES)

        self.instruction_table = {}

        self.issue_slot_labels = []
        self.add_sub_reservation_station_labels = []
        self.mul_div_reservation_station_labels = []
        self.load_store_reservation_station_labels = []
        self.text_editor = QCodeEditor(self)
        self.timing_table = QTableWidget(self)
        self.text_editor_status_label = QLabel('Pass', self)
        self.step_button = QPushButton('Step', self)
        self.run_button = QPushButton('Run', self)
        self.load_button = QPushButton('Load Program', self)
        self.add_sub_num_cycles_textbox = QLineEdit(str(ADD_SUB_LATENCY_CYCLES), self)
        self.mul_div_num_cycles_textbox = QLineEdit(str(MUL_DIV_LATENCY_CYCLES), self)
        self.load_store_num_cycles_textbox = QLineEdit(str(LOAD_STORE_LATENCY_CYCLES), self)
        self.load_store_num_cycles_label = QLabel('No. Cycles for Load/Store', self)
        self.add_sub_num_cycles_label = QLabel('No. Cycles for Add/Sub', self)
        self.mul_div_num_cycles_label = QLabel('No. Cycles for Mul/Div', self)

        self.init_text_editor()
        self.init_timing_table()
        self.init_issue_slot_labels()
        self.init_add_sub_reservation_station_labels()
        self.init_mul_div_reservation_station_labels()
        self.init_load_store_reservation_station_labels()
        self.init_buttons()
        self.init_textboxes()

        self.statusBar().showMessage('Status bar')
        self.setGeometry(300, 300, 1610, 550)
        self.setWindowTitle('ToMasulator')
        self.show()

    def init_text_editor(self):
        self.text_editor.move(10, 10)
        self.text_editor.resize(250, 200)
        self.text_editor.setFont(QFont('Consolas', 14))
        self.text_editor.setPlainText(DEFAULT_PROGRAM)

        self.text_editor_status_label.move(10, 220)
        self.text_editor_status_label.resize(250, 25)
        self.text_editor_status_label.setFont(QFont('Consolas', 14))
        self.text_editor_status_label.setStyleSheet("background-color: green;")

    def init_timing_table(self):
        self.timing_table.resize(900, 370)
        self.timing_table.move(700, 10)
        self.timing_table.setRowCount(50)
        self.timing_table.setColumnCount(200)
        self.timing_table.setFont(QFont('Consolas', 12))
        headers = ['']
        for i in range(500):
            headers.append(str(i + 1))
        self.timing_table.setHorizontalHeaderLabels(headers)
        self.timing_table.setVerticalHeaderLabels(headers)

    def clear_timing_table(self):
        for row in range(50):
            for col in range(200):
                item_id = QTableWidgetItem("")
                self.timing_table.setItem(row + 1, col + 1, item_id)

    def set_timing_table_row_labels(self, names):
        self.clear_timing_table()
        for row, name in enumerate(names):
            item_id = QTableWidgetItem(name)
            self.timing_table.setItem(row+1, 0, item_id)
        self.timing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def init_issue_slot_labels(self):
        # FIXME: constant 3
        for i in range(3):
            self.issue_slot_labels.append(QLabel("", self))
            self.issue_slot_labels[i].move(300, 310 - i * 30)
            self.issue_slot_labels[i].setFont(QFont('Consolas', 14))
            self.issue_slot_labels[i].setStyleSheet("background-color: white;border: 1px solid black;")
            self.issue_slot_labels[i].resize(220, 30)
        issue_slot_name_label = QLabel('Instruction queue', self)
        issue_slot_name_label.setFont(QFont('sans-serif', 12))
        issue_slot_name_label.adjustSize()
        # FIXME 3
        issue_slot_name_label.move(350, 310 - 3*30)

    def init_add_sub_reservation_station_labels(self):
        issue_slot_name_label = QLabel('Add/Sub RS', self)
        issue_slot_name_label.setFont(QFont('sans-serif', 12))
        issue_slot_name_label.adjustSize()
        issue_slot_name_label.move(260, 390)
        for i in range(len(self.cpu.add_sub_reservation_stations)):
            self.add_sub_reservation_station_labels.append(QLabel("", self))
            self.add_sub_reservation_station_labels[i].move(260, 410 + i * 30)
            self.add_sub_reservation_station_labels[i].setFont(QFont('Consolas', 14))
            self.add_sub_reservation_station_labels[i].setStyleSheet("background-color: white;border: 1px solid black;")
            self.add_sub_reservation_station_labels[i].resize(220, 30)

    def init_mul_div_reservation_station_labels(self):
        issue_slot_name_label = QLabel('Mul/Div RS', self)
        issue_slot_name_label.setFont(QFont('Sans-serif', 12))
        issue_slot_name_label.adjustSize()
        issue_slot_name_label.move(500, 390)
        for i in range(len(self.cpu.mul_div_reservation_stations)):
            self.mul_div_reservation_station_labels.append(QLabel("", self))
            self.mul_div_reservation_station_labels[i].move(500, 410 + i * 30)
            self.mul_div_reservation_station_labels[i].setFont(QFont('Consolas', 14))
            self.mul_div_reservation_station_labels[i].setStyleSheet("background-color: white;border: 1px solid black;")
            self.mul_div_reservation_station_labels[i].resize(220, 30)

    def init_load_store_reservation_station_labels(self):
        issue_slot_name_label = QLabel('Load/Store RS', self)
        issue_slot_name_label.setFont(QFont('Sans-serif', 12))
        issue_slot_name_label.adjustSize()
        issue_slot_name_label.move(20, 390)
        for i in range(len(self.cpu.load_store_reservation_stations)):
            self.load_store_reservation_station_labels.append(QLabel("", self))
            self.load_store_reservation_station_labels[i].move(20, 410 + i * 30)
            self.load_store_reservation_station_labels[i].setFont(QFont('Consolas', 14))
            self.load_store_reservation_station_labels[i].setStyleSheet("background-color: white;border: 1px solid black;")
            self.load_store_reservation_station_labels[i].resize(220, 30)

    def init_buttons(self):
        self.load_button.setToolTip('Load the program into the issue buffer')
        self.load_button.move(300, 10)
        self.load_button.adjustSize()
        self.load_button.clicked.connect(self.load_program_button_pressed)

        self.step_button.setToolTip('Step one cycle')
        self.step_button.move(300, 40)
        self.step_button.adjustSize()
        self.step_button.clicked.connect(self.step_button_pressed)

        self.run_button.setToolTip('Run all the code')
        self.run_button.move(300, 70)
        self.run_button.adjustSize()
        self.run_button.clicked.connect(self.run_button_pressed)

    def init_textboxes(self):
        self.load_store_num_cycles_textbox.move(550, 10)
        self.load_store_num_cycles_textbox.resize(50, 20)
        self.load_store_num_cycles_label.move(400, 15)
        self.load_store_num_cycles_label.adjustSize()

        self.add_sub_num_cycles_textbox.move(550, 35)
        self.add_sub_num_cycles_textbox.resize(50, 20)
        self.add_sub_num_cycles_label.move(400, 40)
        self.add_sub_num_cycles_label.adjustSize()

        self.mul_div_num_cycles_textbox.move(550, 60)
        self.mul_div_num_cycles_textbox.resize(50, 20)
        self.mul_div_num_cycles_label.move(400, 65)
        self.mul_div_num_cycles_label.adjustSize()

    def update_text_editor_visual(self, assembly_succeeded, offending_line):
        if assembly_succeeded:
            self.text_editor_status_label.setText("Pass")
            self.text_editor_status_label.setStyleSheet("background-color: green;")
            self.text_editor.clear_highlight()
        else:
            self.text_editor_status_label.setText("Error at line " + str(offending_line))
            self.text_editor_status_label.setStyleSheet("background-color: red;")
            self.text_editor.clear_highlight()
            self.text_editor.highlight_line(offending_line, "red")

    def update_instruction_queue_visual(self):
        for i, slot_label in enumerate(self.issue_slot_labels):
            if i < len(self.cpu.instruction_queue.instructions):
                slot_label.setText(self.cpu.instruction_queue[i].raw_text)
            else:
                slot_label.setText("")

    def update_reservation_station_visual(self):
        for i, label in enumerate(self.add_sub_reservation_station_labels):
            label.setStyleSheet("background-color: white; border: 1px solid black;")
            if self.cpu.add_sub_reservation_stations[i].state != self.cpu.add_sub_reservation_stations[i].State.FREE:
                label.setText(self.cpu.add_sub_reservation_stations[i].instruction.raw_text)
                if self.cpu.add_sub_reservation_stations[i].state == self.cpu.add_sub_reservation_stations[i].State.ISSUED:
                    label.setStyleSheet("background-color: lightgreen; border: 1px solid black;")
            else:
                label.setText("")
        for i, label in enumerate(self.mul_div_reservation_station_labels):
            label.setStyleSheet("background-color: white; border: 1px solid black;")
            if self.cpu.mul_div_reservation_stations[i].state != self.cpu.mul_div_reservation_stations[i].State.FREE:
                label.setText(self.cpu.mul_div_reservation_stations[i].instruction.raw_text)
                if self.cpu.mul_div_reservation_stations[i].state == self.cpu.mul_div_reservation_stations[i].State.ISSUED:
                    label.setStyleSheet("background-color: lightgreen; border: 1px solid black;")
            else:
                label.setText("")
        for i, label in enumerate(self.load_store_reservation_station_labels):
            label.setStyleSheet("background-color: white; border: 1px solid black;")
            if self.cpu.load_store_reservation_stations[i].state != self.cpu.load_store_reservation_stations[i].State.FREE:
                label.setText(self.cpu.load_store_reservation_stations[i].instruction.raw_text)
                if self.cpu.load_store_reservation_stations[i].state == self.cpu.load_store_reservation_stations[i].State.ISSUED:
                    label.setStyleSheet("background-color: lightgreen; border: 1px solid black;")
            else:
                label.setText("")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.white)
        painter.drawLine(400, 330, 400, 380)
        painter.drawLine(120, 380, 600, 380)
        painter.drawLine(120, 380, 120, 420)
        painter.drawLine(400, 380, 400, 420)
        painter.drawLine(600, 380, 600, 420)

    def update_timing_table_instructions_visual(self, instructions):
        self.instruction_table = {}
        for i, inst in enumerate(instructions):
            self.instruction_table[id(inst)] = i + 1
        inst_names = []
        for instruction in instructions:
            inst_names.append(instruction.raw_text)
        self.set_timing_table_row_labels(inst_names)

    def update_timing_table_content_visual(self):
        all_reservation_stations = \
            self.cpu.add_sub_reservation_stations + self.cpu.mul_div_reservation_stations + self.cpu.load_store_reservation_stations
        for rs in all_reservation_stations:
            state = ""
            if rs.state == rs.State.FREE:
                continue
            elif rs.state == rs.State.ISSUED:
                state = "I"
            elif rs.state == rs.State.EXECUTING:
                state = "E"
            elif rs.state == rs.State.WAITING:
                state = "-"
            elif rs.state == rs.State.ATTEMPT_MEMORY_ACCESS:
                state = "-"
            elif rs.state == rs.State.MEMORY:
                state = "M"
            elif rs.state == rs.State.ATTEMPT_WRITE:
                state = "-"
            elif rs.state == rs.State.WRITE_BACK:
                state = "W"

            item_id = QTableWidgetItem(state)
            self.timing_table.setItem(self.instruction_table[id(rs.instruction)], self.cpu.cycle_count, item_id)

    def step_button_pressed(self):
        self.cpu.tick()
        self.update_reservation_station_visual()
        self.update_instruction_queue_visual()
        self.update_timing_table_content_visual()

    def run_button_pressed(self):
        for i in range(300):
            self.step_button_pressed()

    def load_program_button_pressed(self):
        raw_assembly_code = self.text_editor.toPlainText().lower()
        success, offending_line, instructions = assemble(raw_assembly_code)
        if success:
            self.set_latency_cycles()
            self.cpu.reset()
            self.cpu.upload_to_memory(instructions)
            self.update_instruction_queue_visual()
            self.update_timing_table_instructions_visual(instructions)
        self.update_text_editor_visual(success, offending_line)
        self.update_reservation_station_visual()

    def set_latency_cycles(self):
        add_sub_num_cycles = self.cpu.add_sub_latency_cycles
        mul_div_num_cycles = self.cpu.mul_div_latency_cycles
        load_store_num_cycles = self.cpu.load_store_latency_cycles
        try:
            num_cycles = int(self.add_sub_num_cycles_textbox.text())
            if num_cycles > 0:
                add_sub_num_cycles = num_cycles
        except ValueError:
            pass
        try:
            num_cycles = int(self.mul_div_num_cycles_textbox.text())
            if num_cycles > 0:
                mul_div_num_cycles = num_cycles
        except ValueError:
            pass
        try:
            num_cycles = int(self.load_store_num_cycles_textbox.text())
            if num_cycles > 0:
                load_store_num_cycles = num_cycles
        except ValueError:
            pass

        self.cpu.set_latency_cycles(add_sub_num_cycles, mul_div_num_cycles, load_store_num_cycles)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
