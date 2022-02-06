from typing import List

from PyQt5.QtWidgets import (QPushButton, QLabel, QMainWindow, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QGroupBox, QFrame, QVBoxLayout, QHBoxLayout)
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QPoint

from custom_editor import QCodeEditor
from assembler import assemble
from window_settingd import UiSettings
# from controller import Controller


DEFAULT_PROGRAM = \
    "fsw  f1, 0(x1) \nfadd f1, f2, f3 \nfsub f3, f4, f1\nfmul f5, f10, f10\n" \
    "fadd f8, f2, f3 \nfsub f9, f4, f6\nfmul f10, f10, f1\n"

MAX_CYCLES_EXECUTED = 300


class MainWindow(QMainWindow):
    def __init__(self, pos_x, pos_y, width, height, title, controller):
        super().__init__()

        self.controller = controller
        self.instruction_table = {}

        self.main_frame = QFrame(self)
        self.setCentralWidget(self.main_frame)

        self.instruction_queue_labels: List[QLabel] = []
        self.add_sub_reservation_station_labels: List[QLabel] = []
        self.mul_div_reservation_station_labels: List[QLabel] = []
        self.load_store_reservation_station_labels: List[QLabel] = []
        self.code_editor_status_label = QLabel('Pass', self.main_frame)
        self.code_editor = QCodeEditor(self.main_frame)
        self.timing_table = QTableWidget(self.main_frame)

        self.step_button = QPushButton('Step')
        self.run_button = QPushButton('Run')
        self.load_button = QPushButton('Load / Reset')

        self.load_store_num_cycles_textbox = QLineEdit(str(self.controller.get_num_cycles_load_store()))
        self.add_sub_num_cycles_textbox = QLineEdit(str(self.controller.get_num_cycles_add_sub()))
        self.mul_div_num_cycles_textbox = QLineEdit(str(self.controller.get_num_cycles_mul_div()))
        self.load_store_num_cycles_label = QLabel('No. Cycles for Load/Store')
        self.add_sub_num_cycles_label = QLabel('No. Cycles for Add/Sub')
        self.mul_div_num_cycles_label = QLabel('No. Cycles for Mul/Div')

        self.load_store_reservation_station_num_textbox = QLineEdit(str(self.controller.get_num_rerevation_stations_load_store()))
        self.add_sub_reservation_station_num_textbox = QLineEdit(str(self.controller.get_num_rerevation_stations_add_sub()))
        self.mul_div_reservation_station_num_textbox = QLineEdit(str(self.controller.get_num_rerevation_stations_mul_div()))
        self.load_store_reservation_station_num_label = QLabel('No. Load/Store RSs')
        self.add_sub_reservation_station_num_label = QLabel('No. Add/Sub RSs')
        self.mul_div_reservation_station_num_label = QLabel('No. Mul/Div RSs')

        self._init_code_editor()
        self._init_timing_table()
        self._init_instruction_queue_labels()
        self._init_reservation_station_title_labels()
        self._create_all_reservation_station_slot_labels()
        self._init_buttons()
        self._init_cycles_boxes()
        self._init_rs_num_boxes()

        self.statusBar().showMessage('Status:')
        self.setGeometry(pos_x, pos_y, width, height)
        self.setWindowTitle(title)
        self.show()

    def _init_code_editor(self):
        self.code_editor.move(UiSettings.CODE_EDITOR_POS)
        self.code_editor.resize(UiSettings.CODE_EDITOR_SIZE)
        self.code_editor.setFont(UiSettings.CODE_EDITOR_FONT)
        self.code_editor.setPlainText(DEFAULT_PROGRAM)
        self.code_editor_status_label.move(UiSettings.CODE_EDITOR_STATUS_POS)
        self.code_editor_status_label.resize(UiSettings.CODE_EDITOR_STATUS_SIZE)
        self.code_editor_status_label.setFont(UiSettings.CODE_EDITOR_STATUS)
        self.code_editor_status_label.setStyleSheet(UiSettings.GREEN_STYLE)

    def _init_timing_table(self):
        self.timing_table.setRowCount(UiSettings.NUM_ROWS_TIMING_TABLE)
        self.timing_table.setColumnCount(UiSettings.NUM_COLS_TIMING_TABLE)
        self.timing_table.setFont(UiSettings.TIMING_TABEL_FONT)
        self.timing_table.move(UiSettings.TIMING_TABLE_POS)
        self.timing_table.resize(UiSettings.TIMING_TABEL_SIZE)
        headers = ['']
        for i in range(UiSettings.NUM_COLS_TIMING_TABLE):
            headers.append(str(i + 1))
        self.timing_table.setHorizontalHeaderLabels(headers)
        self.timing_table.setVerticalHeaderLabels(headers)

    def _clear_timing_table(self):
        for row in range(UiSettings.NUM_ROWS_TIMING_TABLE):
            for col in range(UiSettings.NUM_COLS_TIMING_TABLE):
                item_id = QTableWidgetItem("")
                self.timing_table.setItem(row + 1, col + 1, item_id)

    def _set_timing_table_row_labels(self, names):
        self._clear_timing_table()
        for row, name in enumerate(names):
            item_id = QTableWidgetItem(name)
            self.timing_table.setItem(row+1, 0, item_id)
        self.timing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def _init_instruction_queue_labels(self):
        num_slots = self.controller.get_num_instruction_queue_slots()
        issue_slot_name_label = QLabel('Instruction queue', self.main_frame)
        issue_slot_name_label.setFont(UiSettings.SLOT_TITLE_FONT)
        issue_slot_name_label.adjustSize()
        issue_slot_name_label.move(UiSettings.INSTRUCTION_QUEUE_TITLE_POS - QPoint(0, num_slots * UiSettings.SLOT_HEIGHT))
        for i in range(num_slots):
            self.instruction_queue_labels.append(QLabel("", self.main_frame))
            self.instruction_queue_labels[i].setFont(UiSettings.SLOT_FONT)
            self.instruction_queue_labels[i].setStyleSheet(UiSettings.WHITE_STYLE)
            self.instruction_queue_labels[i].move(UiSettings.INSTRUCTION_QUEUE_POS - QPoint(0, i * UiSettings.SLOT_HEIGHT))
            self.instruction_queue_labels[i].resize(UiSettings.SLOT_SIZE)

    def _init_reservation_station_title_labels(self):
        load_store_name_label = QLabel('Load/Store RS', self.main_frame)
        load_store_name_label.setFont(UiSettings.SLOT_TITLE_FONT)
        load_store_name_label.adjustSize()
        load_store_name_label.move(UiSettings.LOAD_STORE_RS_TITLE_POS)

        add_sub_name_label = QLabel('Add/Sub RS', self.main_frame)
        add_sub_name_label.setFont(UiSettings.SLOT_TITLE_FONT)
        add_sub_name_label.adjustSize()
        add_sub_name_label.move(UiSettings.ADD_SUB_RS_TITLE_POS)

        mul_div_name_label = QLabel('Mul/Div RS', self.main_frame)
        mul_div_name_label.setFont(UiSettings.SLOT_TITLE_FONT)
        mul_div_name_label.adjustSize()
        mul_div_name_label.move(UiSettings.MUL_DIV_RS_TITLE_POS)

    def _create_all_reservation_station_slot_labels(self):
        self._create_reservation_station_slot_labels(
            rs_labels=self.load_store_reservation_station_labels,
            get_num_rs=self.controller.get_num_rerevation_stations_load_store,
            pos=UiSettings.LOAD_STORE_RS_SLOT_POS
        )
        self._create_reservation_station_slot_labels(
            rs_labels=self.add_sub_reservation_station_labels,
            get_num_rs=self.controller.get_num_rerevation_stations_add_sub,
            pos=UiSettings.ADD_SUB_RS_SLOT_POS
        )
        self._create_reservation_station_slot_labels(
            rs_labels=self.mul_div_reservation_station_labels,
            get_num_rs=self.controller.get_num_rerevation_stations_mul_div,
            pos=UiSettings.MUL_DIV_RS_SLOT_POS
        )

    def _create_reservation_station_slot_labels(self, rs_labels, get_num_rs, pos):
        for label in rs_labels:
            label.deleteLater()
        rs_labels.clear()
        for i in range(get_num_rs()):
            rs_labels.append(QLabel("", self.main_frame))
            rs_labels[i].show()
            rs_labels[i].setFont(UiSettings.SLOT_FONT)
            rs_labels[i].setStyleSheet(UiSettings.WHITE_STYLE)
            rs_labels[i].move(pos + QPoint(0, i * UiSettings.SLOT_HEIGHT))
            rs_labels[i].resize(UiSettings.SLOT_SIZE)

    def _init_buttons(self):
        self.load_button.setToolTip('Load the program into the issue buffer')
        self.load_button.setFont(UiSettings.BUTTONS_FONT)
        self.load_button.clicked.connect(self._load_reset_button_pressed)
        self.step_button.setToolTip('Step one cycle')
        self.step_button.setFont(UiSettings.BUTTONS_FONT)
        self.step_button.clicked.connect(self._step_button_pressed)
        self.run_button.setToolTip('Run all the code')
        self.run_button.setFont(UiSettings.BUTTONS_FONT)
        self.run_button.clicked.connect(self._run_button_pressed)

        buttons_group = QGroupBox("", self.main_frame)
        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.step_button)
        layout.addWidget(self.run_button)
        buttons_group.setLayout(layout)
        buttons_group.move(UiSettings.BUTTONS_POS)
        buttons_group.adjustSize()

    def _init_cycles_boxes(self):
        num_cycles_group = QGroupBox("", self.main_frame)
        outer_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        self.load_store_num_cycles_label.setFont(UiSettings.TEXT_BOXES_FONT)
        self.add_sub_num_cycles_label.setFont(UiSettings.TEXT_BOXES_FONT)
        self.mul_div_num_cycles_label.setFont(UiSettings.TEXT_BOXES_FONT)
        self.load_store_num_cycles_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        self.add_sub_num_cycles_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        self.mul_div_num_cycles_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        left_layout.addWidget(self.load_store_num_cycles_label)
        left_layout.addWidget(self.add_sub_num_cycles_label)
        left_layout.addWidget(self.mul_div_num_cycles_label)
        right_layout.addWidget(self.load_store_num_cycles_textbox)
        right_layout.addWidget(self.add_sub_num_cycles_textbox)
        right_layout.addWidget(self.mul_div_num_cycles_textbox)
        outer_layout.addLayout(left_layout)
        outer_layout.addLayout(right_layout)
        num_cycles_group.setLayout(outer_layout)
        num_cycles_group.move(UiSettings.NUM_CYCLES_TEXTBOX_POS)
        num_cycles_group.resize(UiSettings.NUM_CYCLES_TEXTBOX_SIZE)

    def _init_rs_num_boxes(self):
        rs_num_group = QGroupBox("", self.main_frame)
        outer_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        self.load_store_reservation_station_num_label.setFont(UiSettings.TEXT_BOXES_FONT)
        self.add_sub_reservation_station_num_label.setFont(UiSettings.TEXT_BOXES_FONT)
        self.mul_div_reservation_station_num_label.setFont(UiSettings.TEXT_BOXES_FONT)
        left_layout.addWidget(self.load_store_reservation_station_num_label)
        left_layout.addWidget(self.add_sub_reservation_station_num_label)
        left_layout.addWidget(self.mul_div_reservation_station_num_label)
        right_layout.addWidget(self.load_store_reservation_station_num_textbox)
        right_layout.addWidget(self.add_sub_reservation_station_num_textbox)
        right_layout.addWidget(self.mul_div_reservation_station_num_textbox)
        self.load_store_reservation_station_num_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        self.add_sub_reservation_station_num_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        self.mul_div_reservation_station_num_textbox.setMaximumSize(UiSettings.TEXT_BOXES_MAX_SIZE)
        outer_layout.addLayout(left_layout)
        outer_layout.addLayout(right_layout)
        rs_num_group.setLayout(outer_layout)
        rs_num_group.move(UiSettings.NUM_RS_TEXTBOX_POS)
        rs_num_group.resize(UiSettings.NUM_RS_TEXTBOX_SIZE)

    def _update_code_editor_visual(self, assembly_succeeded, offending_line):
        if assembly_succeeded:
            self.code_editor_status_label.setText("Pass")
            self.code_editor_status_label.setStyleSheet(UiSettings.GREEN_STYLE)
            self.code_editor.clear_highlight()
        else:
            self.code_editor_status_label.setText("Error at line " + str(offending_line))
            self.code_editor_status_label.setStyleSheet(UiSettings.RED_STYLE)
            self.code_editor.clear_highlight()
            self.code_editor.highlight_line(offending_line, UiSettings.RED_COLOR)

    def _update_instruction_queue_visual(self):
        insts = self.controller.get_instruction_texts_in_queue()
        num_insts_in_queue = len(insts)
        for i, slot_label in enumerate(self.instruction_queue_labels):
            if i < num_insts_in_queue:
                slot_label.setText(insts[i])
            else:
                slot_label.setText("")

    def _update_reservation_stations_visual(self):
        for i, rs_label in enumerate(self.load_store_reservation_station_labels):
            rs_label.setStyleSheet(UiSettings.WHITE_STYLE)
            if not self.controller.load_store_reservation_station_is_free(i):
                rs_label.setText(self.controller.get_load_store_reservation_station_instruction_text(i))
                if self.controller.load_store_reservation_station_is_just_issued(i):
                    rs_label.setStyleSheet(UiSettings.GREEN_STYLE)
            else:
                rs_label.setText("")
        for i, rs_label in enumerate(self.add_sub_reservation_station_labels):
            rs_label.setStyleSheet(UiSettings.WHITE_STYLE)
            if not self.controller.add_sub_reservation_station_is_free(i):
                rs_label.setText(self.controller.get_add_sub_reservation_station_instruction_text(i))
                if self.controller.add_sub_reservation_station_is_just_issued(i):
                    rs_label.setStyleSheet(UiSettings.GREEN_STYLE)
            else:
                rs_label.setText("")
        for i, rs_label in enumerate(self.mul_div_reservation_station_labels):
            rs_label.setStyleSheet(UiSettings.WHITE_STYLE)
            if not self.controller.mul_div_reservation_station_is_free(i):
                rs_label.setText(self.controller.get_mul_div_reservation_station_instruction_text(i))
                if self.controller.mul_div_reservation_station_is_just_issued(i):
                    rs_label.setStyleSheet(UiSettings.GREEN_STYLE)
            else:
                rs_label.setText("")

    def _update_timing_table_instructions_visual(self, instructions):
        self.instruction_table = {}
        for i, inst in enumerate(instructions):
            self.instruction_table[id(inst)] = i + 1
        inst_names = []
        for instruction in instructions:
            inst_names.append(instruction.raw_text)
        self._set_timing_table_row_labels(inst_names)

    def _update_timing_table_content_visual(self):
        all_rs_info = self.controller.get_reservation_stations_info()

        for rs_info in all_rs_info:
            rs_state = rs_info[0]
            rs_inst_id = rs_info[1]
            table_state = ""
            if rs_state == "FREE":
                continue
            elif rs_state == "JUST_ISSUED":
                table_state = "I"
            elif rs_state == "EXECUTING":
                table_state = "E"
            elif rs_state == "WAITING":
                table_state = "-"
            elif rs_state == "ATTEMPT_MEMORY_ACCESS":
                table_state = "-"
            elif rs_state == "MEMORY":
                table_state = "M"
            elif rs_state == "ATTEMPT_WRITE":
                table_state = "-"
            elif rs_state == "WRITE_BACK":
                table_state = "W"

            item_id = QTableWidgetItem(table_state)
            self.timing_table.setItem(self.instruction_table[rs_inst_id], self.controller.get_cycle_count(), item_id)

    def _step_button_pressed(self):
        self.controller.tick()
        self._update_reservation_stations_visual()
        self._update_instruction_queue_visual()
        self._update_timing_table_content_visual()

    def _run_button_pressed(self):
        for i in range(MAX_CYCLES_EXECUTED):
            self._step_button_pressed()

    def _load_reset_button_pressed(self):
        raw_assembly_code = self.code_editor.toPlainText().lower()
        success, offending_line, instructions = assemble(raw_assembly_code)
        if success:
            self._set_latency_cycles()
            self._set_num_reservation_stations()
            self._create_all_reservation_station_slot_labels()
            self.controller.reset()
            self.controller.upload_to_memory(instructions)
            self._update_instruction_queue_visual()
            self._update_timing_table_instructions_visual(instructions)
        self._update_code_editor_visual(success, offending_line)
        self._update_reservation_stations_visual()

    def _set_latency_cycles(self):
        num_cycles_load_store = self.controller.get_num_cycles_load_store()
        num_cycles_add_sub = self.controller.get_num_cycles_add_sub()
        num_cycles_mul_div = self.controller.get_num_cycles_mul_div()
        try:
            num_cycles = int(self.load_store_num_cycles_textbox.text())
            if num_cycles > 0:
                num_cycles_load_store = num_cycles
        except ValueError:
            pass
        try:
            num_cycles = int(self.add_sub_num_cycles_textbox.text())
            if num_cycles > 0:
                num_cycles_add_sub = num_cycles
        except ValueError:
            pass
        try:
            num_cycles = int(self.mul_div_num_cycles_textbox.text())
            if num_cycles > 0:
                num_cycles_mul_div = num_cycles
        except ValueError:
            pass

        self.controller.set_num_cycles(num_cycles_load_store, num_cycles_add_sub, num_cycles_mul_div)

    def _set_num_reservation_stations(self):
        max_rs_num = 10
        load_store_rs_nums = self.controller.get_num_rerevation_stations_add_sub()
        add_sub_rs_nums = self.controller.get_num_rerevation_stations_add_sub()
        mul_div_rs_nums = self.controller.get_num_rerevation_stations_mul_div()
        try:
            rs_nums = int(self.load_store_reservation_station_num_textbox.text())
            if rs_nums > 0:
                load_store_rs_nums = rs_nums if rs_nums <= max_rs_num else max_rs_num
        except ValueError:
            pass
        try:
            rs_nums = int(self.add_sub_reservation_station_num_textbox.text())
            if rs_nums > 0:
                add_sub_rs_nums = rs_nums if rs_nums <= max_rs_num else max_rs_num
        except ValueError:
            pass
        try:
            rs_nums = int(self.mul_div_reservation_station_num_textbox.text())
            if rs_nums > 0:
                mul_div_rs_nums = rs_nums if rs_nums <= max_rs_num else max_rs_num
        except ValueError:
            pass

        self.controller.set_reservation_station_sizes(load_store_rs_nums, add_sub_rs_nums, mul_div_rs_nums)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(Qt.white)
        painter.drawLine(400, 330, 400, 380)
        painter.drawLine(120, 380, 600, 380)
        painter.drawLine(120, 380, 120, 420)
        painter.drawLine(400, 380, 400, 420)
        painter.drawLine(600, 380, 600, 420)