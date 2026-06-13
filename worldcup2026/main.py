import sys
from PyQt6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    # 后续任务中接入主窗口
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
