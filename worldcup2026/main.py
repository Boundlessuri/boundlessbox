"""2026 世界杯赛程预测工具 — 入口"""

import sys, os

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
