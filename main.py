import sys
from PyQt5.QtWidgets import (QWidget, QToolTip, QPushButton, QApplication, QTextEdit, QLabel, QMainWindow, QGraphicsColorizeEffect)
from PyQt5.QtGui import QFont, QColor
from gui import QCodeEditor

from processor import Processor, InstructionMemory
from assembler import assemble
from instruction import Instruction


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.cpu = Processor()

        self.issue_slot_labels = None
        self.text_editor = QCodeEditor(self)
        self.text_editor_label = QLabel('Pass', self)
        self.step_button = None
        self.load_button = None
        self.init_text_editor()
        self.init_issue_slot_labels()
        self.init_buttons()

        self.statusBar().showMessage('Status bar')
        self.setGeometry(600, 300, 1300, 700)
        self.setWindowTitle('Tooltips')
        self.show()

    def init_text_editor(self):
        self.text_editor.move(10, 10)
        self.text_editor.resize(250, 200)
        self.text_editor.setFont(QFont('Consolas', 14))
        self.text_editor.setPlainText("fadd   f1, f2, f3 \nfsub   f3, f4, f6\nfmul   f5, f10, f1\nflw    f5, 100(x1)\nfsw    f6, 200(x2)")

        self.text_editor_label.move(10, 220)
        self.text_editor_label.resize(250, 25)
        self.text_editor_label.setFont(QFont('Consolas', 14))
        self.text_editor_label.setStyleSheet("background-color: green;")

    def init_issue_slot_labels(self):
        self.issue_slot_labels = []
        for i in range(3):
            self.issue_slot_labels.append(QLabel('This is label ' + str(i), self))
            self.issue_slot_labels[i].move(300, 120 + i * 30)
            self.issue_slot_labels[i].setFont(QFont('Consolas', 14))
            self.issue_slot_labels[i].setStyleSheet("background-color: white;border: 1px solid black;")
            self.issue_slot_labels[i].resize(200, 30)

    def init_buttons(self):
        QToolTip.setFont(QFont('SansSerif', 10))
        self.setToolTip('This is a <b>QWidget</b> widget')

        self.step_button = QPushButton('Step', self)
        self.step_button.setToolTip('This is a <b>QPushButton</b> widget')
        self.step_button.resize(self.step_button.sizeHint())
        self.step_button.move(300, 50)

        self.step_button.clicked.connect(self.step_button_pressed)

        self.setToolTip('This is a <b>QWidget</b> widget')

        self.load_button = QPushButton('Load Program', self)
        self.load_button.setToolTip('This is a <b>QPushButton</b> widget 2')
        self.load_button.resize(self.step_button.sizeHint())
        self.load_button.move(300, 80)

        self.load_button.clicked.connect(self.load_program_button_pressed)

    def step_button_pressed(self):
        self.text_editor.setPlainText(
            "fadd f1, f2, f3 \nfsub f3, f4, f6\nfmul f5, f10, f1\nflw f5, 100(x1)\nfsw f6, 200(x2)")
        pass

    def load_program_button_pressed(self):
        raw_assembly_code = self.text_editor.toPlainText().lower()
        success, offending_line, instructions = assemble(raw_assembly_code)
        if not success:
            self.text_editor_label.setText("Error at line " + str(offending_line))
            self.text_editor_label.setStyleSheet("background-color: red;")
        else:
            self.text_editor_label.setText("Pass")
            self.text_editor_label.setStyleSheet("background-color: green;")
            self.cpu.reset()
            self.cpu.load(instructions)
            for i, slot_label in enumerate(self.issue_slot_labels):
                if i < len(self.cpu.instruction_issue_queue):
                    slot_label.setText(self.cpu.instruction_issue_queue[i].string)
                else:
                    slot_label.setText("")


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
