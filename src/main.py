import sys

from PyQt5.QtWidgets import QApplication

from controller import Controller
from settings import get_style_from_settings_file


def main():
    app = QApplication(sys.argv)
    app.setStyle(get_style_from_settings_file())

    Controller()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
