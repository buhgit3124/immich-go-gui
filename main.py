# immich_go_gui/main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from PySide6.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()