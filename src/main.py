import sys

from PyQt5.QtWidgets import QApplication

from controller import Controller
from settings import get_style_from_settings_file
from window import MainWindow


WINDOW_WIDTH = 1610
WINDOW_HEIGHT = 600
WINDOW_TITLE = 'ToMasulator'


def main():
    app = QApplication(sys.argv)
    app.setStyle(get_style_from_settings_file())

    controller = Controller()

    main_window = MainWindow(pos_x=300, pos_y=300, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, title=WINDOW_TITLE, controller=controller)
    main_window.load_reset()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
