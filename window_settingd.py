from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtGui import QFont


class UiSettings:
    SLOT_FONT = QFont('Consolas', 14)
    SLOT_TITLE_FONT = QFont('Arial', 11)
    BUTTONS_FONT = QFont('Arial', 10)
    TEXT_BOXES_FONT = QFont('Arial', 10)
    CODE_EDITOR_FONT = QFont('Consolas', 14)
    CODE_EDITOR_STATUS = QFont('Consolas', 14)
    TIMING_TABEL_FONT = QFont('Consolas', 12)

    RED_COLOR = "lightcoral"
    GREEN_COLOR = "lightgreen"
    WHITE_STYLE = "background-color: white; border: 1px solid black;"
    GREEN_STYLE = "background-color: " + GREEN_COLOR + "; font-weight: bold; border: 1px solid black;"
    RED_STYLE = "background-color: " + RED_COLOR + "; font-weight: bold; border: 1px solid black;"

    TOP_POS_Y = 10
    CODE_EDITOR_POS = QPoint(10, TOP_POS_Y)
    CODE_EDITOR_SIZE = QSize(250, 200)
    CODE_EDITOR_STATUS_POS = QPoint(10, 220)
    CODE_EDITOR_STATUS_SIZE = QSize(250, 25)
    TIMING_TABLE_POS = QPoint(700, TOP_POS_Y)
    TIMING_TABEL_SIZE = QSize(900, 370)
    INSTRUCTION_QUEUE_TITLE_POS = QPoint(350, 310)
    INSTRUCTION_QUEUE_POS = QPoint(300, 310)
    SLOT_HEIGHT = 30
    SLOT_SIZE = QSize(220, SLOT_HEIGHT)
    RS_TITLE_POS_Y = 390
    RS_SLOT_POS_Y = 410
    LOAD_STORE_RS_TITLE_POS = QPoint(20, RS_TITLE_POS_Y)
    LOAD_STORE_RS_SLOT_POS = QPoint(20, RS_SLOT_POS_Y)
    ADD_SUB_RS_TITLE_POS = QPoint(260, RS_TITLE_POS_Y)
    ADD_SUB_RS_SLOT_POS = QPoint(260, RS_SLOT_POS_Y)
    MUL_DIV_RS_TITLE_POS = QPoint(500, RS_TITLE_POS_Y)
    MUL_DIV_RS_SLOT_POS = QPoint(500, RS_SLOT_POS_Y)
    BUTTONS_POS = QPoint(280, TOP_POS_Y)
    TEXT_BOXES_MAX_SIZE = QSize(30, 30)
    NUM_CYCLES_TEXTBOX_POS = QPoint(400, TOP_POS_Y)
    NUM_CYCLES_TEXTBOX_SIZE = QSize(220, 80)
    NUM_RS_TEXTBOX_POS = QPoint(400, 100)
    NUM_RS_TEXTBOX_SIZE = NUM_CYCLES_TEXTBOX_SIZE

    NUM_ROWS_TIMING_TABLE = 50
    NUM_COLS_TIMING_TABLE = 200
