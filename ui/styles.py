# immich_go_gui/ui/styles.py
from PySide6.QtWidgets import QTabWidget

def apply_tab_styles(tab_widget: QTabWidget):
    tab_widget.setStyleSheet("""
        QTabBar::tab {
            background: #546E7A;
            padding: 10px 24px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            color: white;
            font-weight: 500;
            margin-right: 2px;
            border: none;
        }
        QTabBar::tab:selected {
            background: #37474F;
            color: white;
            border-bottom: 2px solid #263238;
        }
        QTabBar::tab:hover:!selected {
            background: #455A64;
        }
        QPushButton {
            background: #546E7A;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
        }
        QPushButton:hover {
            background: #455A64;
        }
        QPushButton:pressed {
            background: #37474F;
        }
        QPushButton:disabled {
            background: #B0BEC5;
            color: #90A4AE;
        }
    """)